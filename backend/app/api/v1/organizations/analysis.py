from pathlib import Path
from uuid import UUID

import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.core.permissions import ROLE_ADMIN, ROLE_ANALYST
from app.dependencies.database import get_db
from app.dependencies.organization import require_organization_role
from app.repositories.analysis_run_repository import AnalysisRunRepository
from app.repositories.dataset_version_repository import DatasetVersionRepository
from app.repositories.research_workspace_repository import ResearchWorkspaceRespository
from app.models.organization_member import OrganizationMember
from app.repositories.dataset_repository import DatasetRepository
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    VolatilityAnalysisRequest,
    BetaAnalysisRequest,
    AnalysisRunRequest,
    AnalysisRunResponse,
    SharpeAnalysisRequest,
    SortinoAnalysisRequest,
    VaRAnalysisRequest,
    PortfolioRiskAnalysisRequest,
    PortfolioStressAnalysisRequest,
    PortfolioNamedScenarioAnalysisRequest,
)
from app.schemas.visualization import (
    VisualizationRequest,
    VisualizationResponse,
)
from app.schemas.performace_comparison import PerformanceComparisonRequest
from app.services.analysis.return_analyzer import ReturnAnalyzer
from app.services.analysis.volatility_analyzer import VolatilityAnalyzer
from app.services.analysis.correlation_analyzer import CorrelationAnalyzer
from app.services.analysis.covariance_analyzer import CovarianceAnalyzer
from app.services.analysis.drawdown_analyzer import DrawdownAnalyzer
from app.services.analysis.volume_analyzer import VolumeAnalyzer
from app.services.analysis.price_range_analyzer import PriceRangeAnalyzer
from app.services.analysis.beta_analyzer import BetaAnalyzer
from app.services.analysis.analysis_service import AnalysisService
from app.services.analysis.sharpe_analyzer import SharpeAnalyzer
from app.services.analysis.sortino_analyzer import SortinoAnalyzer
from app.services.analysis.var_analyzer import VaRAnalyzer
from app.services.analysis.cvar_analyzer import CVaRAnalyzer
from app.services.analysis.portfolio.portfolio_risk_engine import PortfolioRiskEngine
from app.services.analysis.portfolio.portfolio_stress_engine import PortfolioStressEngine
from app.services.analysis.portfolio.portfolio_validator import PortfolioValidationError
from app.services.analysis.performance_comparison_service import PerformanceComparisonService
from app.services.visualization.visualization_service import VisualizationService
from app.services.execution.market_data_loader import ExecutionMarketDataLoader

router = APIRouter()


ANALYSIS_ROOT = (
    Path(__file__).resolve().parents[4] / "storage"
).resolve()


#Helpers

def _resolve_file(
    file_path: str
) -> Path:
    """
    Resolve a market data file safely inside Quantara storage.
    """

    path = (ANALYSIS_ROOT / file_path).resolve()

    if(path != ANALYSIS_ROOT and ANALYSIS_ROOT not in path.parents):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid analysis file path",
        )

    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis file not found",
        )

    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anlysis path is not a file",
        )

    return path


def _load_dataframe(file_path: str) -> pd.DataFrame:
    """
    Load supported market-data files into a DataFrame.
    """

    suffix = file_path.suffix.lower()

    try:
        if suffix == ".csv":
            return pd.read_csv(file_path)

        if suffix in {".parquet", ".pq"}:
            return pd.read_parquet(file_path)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "Unsupported analysis file format. Supported formats: CSV and Parquet."
        ),
    )


def _validate_dataset(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    membership: OrganizationMember,
    db,
):
    """
    Validate that the dataset belongs to the requested organization/project.
    """

    repository = DatasetRepository(db)

    dataset = repository.get_by_id_in_project(
        dataset_id=dataset_id,
        organization_id=organization_id,
        project_id=project_id,
    )

    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found.",
        )

    return dataset



##Returns

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/returns",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_returns(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: AnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db)
):
    """
    Analyze simple and logarithmic returns.
    """

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    # Market-data datasets may expose the price field as `price`
    # rather than `close`. The existing ReturnAnalyzer operates on the canonical `close`
    # field, so normalize the dataframe at the API boundary without modifying the analyzer.
    if "close" not in dataframe.columns and "price" in dataframe.columns:
        dataframe = dataframe.rename(
            columns={
                "price": "close",
            }
        )

    #Returns must follow chronological order.
    if "timestamp" in dataframe.columns:
        timestamp = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
            utc=True,
        )

        if timestamp.isna().any():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timestamp column contains invalid or null values.",
            )

        dataframe = (
            dataframe.assign(
                timestamp=timestamp,
            )
            .sort_values(
                "timestamp"
            )
            .reset_index(
                drop=True
            )
        )

    try:
        result = ReturnAnalyzer().analyze(dataframe)

        return {
            "result": result,
        }
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

##Volatility

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/volatility",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_volatility(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: VolatilityAnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze periodic and annualized volatility.
    """

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    #Market-data datasets may expose the price field as `price`
    #rather than `close`. Normalize it at the API booundary so
    #the existing VolatilityAnalyzer can operate on the canonical `close` field.

    if "close" not in dataframe.columns and "price" in dataframe.columns:
        dataframe = dataframe.rename(
            columns={
                "price": "close",
            }
        )

    #Keep the volatility calculation chronological when timestamps are available
    if "timestamp" in dataframe.columns:
        timestamp = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
            utc=True,
        )

        if timestamp.isna().any():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timestamp column contains invalid or null values.",
            )

        dataframe = (
            dataframe.assign(
                timestamp=timestamp,
            )
            .sort_values(
                "timestamp"
            )
            .reset_index(
                drop=True
            )
        )

    try:
        result = VolatilityAnalyzer().analyze(
            dataframe,
            periods_per_year = data.periods_per_year,
        )

        return {
            "result": result,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


## Correlation

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/correlation",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_correlation(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: AnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db)
):
    "Analyze Pearson correlation between symbol returns."

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    # Market-data datasets may expose the price field as `price`
    # rather than `close`. Normalize it at the API boundary so
    # the existing CorrelationAnalyzer can operate on `close`.
    if "close" not in dataframe.columns and "price" in dataframe.columns:
        dataframe = dataframe.rename(
            columns={
                "price": "close",
            }
        )

    # Correlation is calculated from returns, so observations
    # must be processed chronologically.
    if "timestamp" in dataframe.columns:
        timestamp = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
            utc=True,
        )

        if timestamp.isna().any():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timestamp column contains invalid or null values.",
            )

        dataframe = (
            dataframe.assign(
                timestamp=timestamp,
            )
            .sort_values(
                ["symbol", "timestamp"]
            )
            .reset_index(
                drop=True
            )
        )

    try:
        result = CorrelationAnalyzer().analyze(dataframe)

        return {
            "result": result,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


##Covariance

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/covariance",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_covariance(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: AnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze sample covariance between symbol returns.
    """

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    # Market-data datasets may expose the price field as `price`
    # rather than `close`. Normalize it at the API boundary so
    # the existing CorrelationAnalyzer can operate on `close`.
    if "close" not in dataframe.columns and "price" in dataframe.columns:
        dataframe = dataframe.rename(
            columns={
                "price": "close",
            }
        )

    # Correlation is calculated from returns, so observations
    # must be processed chronologically.
    if "timestamp" in dataframe.columns:
        timestamp = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
            utc=True,
        )

        if timestamp.isna().any():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timestamp column contains invalid or null values.",
            )

        dataframe = (
            dataframe.assign(
                timestamp=timestamp,
            )
            .sort_values(
                ["symbol", "timestamp"]
            )
            .reset_index(
                drop=True
            )
        )

    try:
        result = CovarianceAnalyzer().analyze(dataframe)

        return {
            "result": result,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

##Drawdown

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/drawdown",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_drawdown(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: AnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze maximum drawdown and recovery characteristics.
    """

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    #Market-data datasets may expose the price field as `price`
    #rather than `close`. Normalize it at the API booundary so
    #the existing VolatilityAnalyzer can operate on the canonical `close` field.

    if "close" not in dataframe.columns and "price" in dataframe.columns:
        dataframe = dataframe.rename(
            columns={
                "price": "close",
            }
        )

    #Keep the volatility calculation chronological when timestamps are available
    if "timestamp" in dataframe.columns:
        timestamp = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
            utc=True,
        )

        if timestamp.isna().any():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timestamp column contains invalid or null values.",
            )

        dataframe = (
            dataframe.assign(
                timestamp=timestamp,
            )
            .sort_values(
                "timestamp"
            )
            .reset_index(
                drop=True
            )
        )

    try:
        result = DrawdownAnalyzer().analyze(dataframe)

        return {
            "result": result,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

#Volume

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/volume",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_volume(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: AnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze trading volume statistics and activity.
    """

    dataset = _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    try:
        result = VolumeAnalyzer().analyze(dataframe)

        return {
            "result": result,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

##Price Range

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/price-range",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_price_range(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: AnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze intrabar price ranges.
    """

    dataset = _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    try:
        result = PriceRangeAnalyzer().analyze(dataframe)

        return {
            "result": result,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

##Beta Analyzer

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/beta",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_beta(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: BetaAnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze asset beta relative to a benchmark.
    """

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    # Market-data datasets may expose the price field as `price`
    # rather than `close`. Normalize it at the API boundary so
    # the existing BetaAnalyzer can operate on `close`.
    if "close" not in dataframe.columns and "price" in dataframe.columns:
        dataframe = dataframe.rename(
            columns={
                "price": "close",
            }
        )

    # Beta is calculated from returns, so observations must be
    # processed chronologically.
    if "timestamp" in dataframe.columns:
        timestamp = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
            utc=True,
        )

        if timestamp.isna().any():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timestamp column contains invalid or null values.",
            )

        dataframe = (
            dataframe.assign(
                timestamp=timestamp,
            )
            .sort_values(
                ["symbol", "timestamp"],
            )
            .reset_index(
                drop=True,
            )
        )

    try:
        result = BetaAnalyzer().analyze(
            dataframe=dataframe,
            asset_symbol=data.asset_symbol,
            benchmark_symbol=data.benchmark_symbol,
        )

        return {
            "result": result,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

##Sortino Analyzer
@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/sortino",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_sortino(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: SortinoAnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """Analyze downside risk and calculate the Sortino ratio."""

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    try:
        result = SortinoAnalyzer().analyze(
            dataframe=dataframe,
            periods_per_year=data.periods_per_year,
            risk_free_rate=data.risk_free_rate,
            target_return=data.target_return,
            symbol=data.symbol,
        )

        return {
            "result": result
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

##Value at Risk

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/var",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_var(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: VaRAnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze Value at Risk using historical or prametric methodology.
    """

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    try:
        result = VaRAnalyzer().analyze(
            dataframe=dataframe,
            confidence_level=data.confidence_level,
            method=data.method,
            periods_per_year=data.periods_per_year,
            symbol=data.symbol,
        )

        return {
            "result": result
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

#CVar

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/cvar",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_cvar(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: VaRAnalysisRequest,
    confidence_level: float = 0.95,
    periods_per_year: int = 252,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    try:
        result = CVaRAnalyzer().analyze(
            dataframe,
            symbol=data.symbol,
            confidence_level=confidence_level,
            periods_per_year=periods_per_year,
        )

        return{
            "result": result
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


##Sharpe

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/sharpe",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_sharpe(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: SharpeAnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze risk adjusted performance using the Sharpe ratio.
    """

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    try:
        result = SharpeAnalyzer().analyze(
            dataframe=dataframe,
            periods_per_year=data.periods_per_year,
            risk_free_rate=data.risk_free_rate,
            symbol=data.asset_symbol,
        )

        return {
            "result": result
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


#Portfolio Risk

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/portfolio-risk",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_portfolio_risk(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: PortfolioRiskAnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze portfolio-level risk using historical market prices and portfolio
    holdings.
    """

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    holdings = pd.DataFrame(
        [
            {
                "symbol": holding.symbol,
                "weight": holding.weight,
            }
            for holding in data.holdings
        ]
    )

    try:
        result = PortfolioRiskEngine(
            periods_per_year=data.periods_per_year,
        ).analyze(
            prices=dataframe,
            holdings=holdings,
        )

        return {
            "result": result,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

# Portfolio Stress

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/portfolio-stress",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_portfolio_stress(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: PortfolioStressAnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    holdings_dataframe = pd.DataFrame(
        [
            {
                "symbol": holding.symbol,
                "weight": holding.weight,
            }
            for holding in data.holdings
        ]
    )

    engine = PortfolioStressEngine()

    try:
        result = engine.analyze(
            holdings=holdings_dataframe,
            shocks=data.shocks,
            scenario_name=data.scenario_name,
        )

        return {
            "result": result,
        }

    except PortfolioValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# Portfolio Named Scenario

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/portfolio-stress/scenario",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_portfolio_named_scenario(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: PortfolioNamedScenarioAnalysisRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze a portfolio under a predefined named stress scenario.
    """

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    _load_dataframe(path)

    holdings = pd.DataFrame(
        [
            {
                "symbol": holding.symbol,
                "weight": holding.weight,
            }
            for holding in data.holdings
        ]
    )

    try:
        result = PortfolioStressEngine().analyze_scenario(
            holdings=holdings,
            scenario_id=data.scenario_id,
        )

        return {
            "result": result
        }

    except PortfolioValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

##Analysis runs

@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/runs",
    response_model=AnalysisRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_analysis_run(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: AnalysisRunRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """Execute an analysis and persist the analysis run."""

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    dataset_version_repository = DatasetVersionRepository(db)

    dataset_version = (
        dataset_version_repository.get_by_id_for_dataset(
            dataset_version_id=data.dataset_version_id,
            dataset_id=dataset_id,
        )
    )

    if dataset_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset version not found.",
        )

    if not dataset_version.storage_uri:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Dataset version has no storage URI.",
        )

    # Validate the optional research workspace against the organization
    # organization and project that own this analysis run.
    if data.research_workspace_id is not None:
        workspace_repository = ResearchWorkspaceRespository(db)

        workspace = workspace_repository.get_by_id(
            workspace_id=data.research_workspace_id,
            organization_id=organization_id,
            project_id=project_id,
        )

        if workspace is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Research workspace not found.",
            )

        # If the workspace is dataset-scoped, it must refer to 
        # the same dataset used by this analysis run.
        if (
            workspace.dataset_id is not None
            and workspace.dataset_id != dataset_id
        ):

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Research workspace does not belong to this dataset.",
            )

        # If the workspace pins a dataset version, it must refer to the exact version
        # used by this analysis run.

        if (
            workspace.dataset_version_id is not None
            and workspace.dataset_version_id != data.dataset_version_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Research workspace is configured for a different "
                    "dataset version."
                ),
            )

    # The dataset version is the authoritative source of market data
    # The client-supplied file_path is retained for API compatibility,
    # but the actual data is loader from DatasetVersion.storage_uri.
    loader = ExecutionMarketDataLoader(ANALYSIS_ROOT)

    dataframe = loader.load(dataset_version.storage_uri)

    repository = AnalysisRunRepository(db)
    service = AnalysisService(repository)

    try:
        return service.run(
            dataframe=dataframe,
            organization_id=organization_id,
            project_id=project_id,
            dataset_id=dataset_id,
            dataset_version_id=data.dataset_version_id,
            analysis_type=data.analysis_type,
            created_by=membership.user_id,
            research_workspace_id=data.research_workspace_id,
            configuration=data.configuration,
            **data.parameters,
        )

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

@router.post(
    "/{organization_id}/projects/{project_id}/dataset/{dataset_id}/analysis/runs/{run_id}/reproduce",
    response_model=AnalysisRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def reproduce_analysis_run(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    run_id: UUID,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    """Reproduce a completed analysis run using its exact dataset version."""

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    repository = AnalysisRunRepository(db)

    source_run = repository.get_by_id(
        analysis_run_id=run_id,
    )

    if source_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found.",
        )

    if (
        source_run.organization_id != organization_id
        or source_run.project_id != project_id
        or source_run.dataset_id != dataset_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found.",
        )

    if source_run.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only completed analysis runs can be reproduced.",
        )

    if source_run.dataset_version_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Analysis run has no dataset version.",
        )

    dataset_version_repository = DatasetVersionRepository(db)

    dataset_version = (
        dataset_version_repository.get_by_id_for_dataset(
            dataset_version_id=source_run.dataset_version_id,
            dataset_id=dataset_id,
        )
    )

    if dataset_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset version for analysis run not found.",
        )

    # Reproduction must use the exact dataset version referenced
    # by the original analysis run.

    loader = ExecutionMarketDataLoader(ANALYSIS_ROOT)
    dataframe = loader.load(dataset_version.storage_uri)


    service = AnalysisService(repository)

    try:

        return service.run(
            dataframe=dataframe,
            organization_id=organization_id,
            project_id=project_id,
            dataset_id=dataset_id,
            dataset_version_id=source_run.dataset_version_id,
            analysis_type=source_run.analysis_type,
            created_by=membership.user_id,
            research_workspace_id=source_run.research_workspace_id,
            configuration=source_run.configuration,
            reproduced_from_id=source_run.id,
            **source_run.parameters,
        )

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

@router.get(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/runs/{run_id}/reproductions",
    response_model=list[AnalysisRunResponse],
    status_code=status.HTTP_200_OK,
)
def list_analysis_run_reproduction(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    run_id: UUID,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    """List direct reproduction created from an analysis run."""

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    repository = AnalysisRunRepository(db)

    source_run = repository.get_by_id(
        analysis_run_id=run_id,
    )

    if source_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found.",
        )

    if (
        source_run.organization_id != organization_id
        or source_run.project_id != project_id
        or source_run.dataset_id != dataset_id
    ):

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found.",
        )

    return repository.list_reproduction(
        analysis_run_id=run_id,
    )

@router.get(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/runs",
    response_model=list[AnalysisRunResponse],
    status_code=status.HTTP_200_OK,
)
def list_analysis_runs(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """
    List persisted analysis runs for a dataset.
    """

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    repository = AnalysisRunRepository(db)

    return repository.list_by_dataset(
        dataset_id=dataset_id,
    )

@router.get(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/runs/{run_id}",
    response_model=AnalysisRunResponse,
    status_code=status.HTTP_200_OK,
)
def get_analysis_run(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    run_id: UUID,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve a persisted analysis run.
    """

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    repository = AnalysisRunRepository(db)

    analysis_run = repository.get_by_id(
        analysis_run_id=run_id,
    )

    if analysis_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found",
        )

    if analysis_run.dataset_id != dataset_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis run not found",
        )

    return analysis_run


@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/performance-comparison",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_performance_comparison(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: PerformanceComparisonRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    """
    Compare performance and risk characteristics across multiple instruments.
    """

    _validate_dataset(
        organization_id,
        project_id,
        dataset_id,
        membership,
        db,
    )

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

    #Market-data datasets may expose the price field as `price` rather than `close`
    if (
        "close" not in dataframe.columns
        and "price" in dataframe.columns
    ):

        dataframe = dataframe.rename(
            columns={
                "price": "close",
            }
        )

    #Performance metrics must be calculated chronologically.
    if "timestamp" in dataframe.columns:
        timestamp = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
            utc=True,
        )

        if timestamp.isna().any():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timestamp column contains invalid or null values."
            )

        dataframe = (
            dataframe.assign(
                timestamp=timestamp,
            )
            .sort_values(
                ["symbol", "timestamp"],
            )
            .reset_index(
                drop=True,
            )
        )

    try:

        result = PerformanceComparisonService().compare(
            dataframe=dataframe,
            symbols=data.symbols,
            periods_per_year=data.periods_per_year,
        )

        return {
            "result": result,
        }

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/{organization_id}/projects/{project_id}/datasets/{dataset_id}/analysis/visualization",
    status_code=status.HTTP_201_CREATED,
    response_model=VisualizationResponse,
)
def analyze_visualization(
    organization_id: UUID,
    project_id: UUID,
    dataset_id: UUID,
    data: VisualizationRequest,
    membership: OrganizationMember = Depends(
        require_organization_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
        )
    ),
    db: Session = Depends(get_db),
):

    _validate_dataset(
        organization_id=organization_id,
        project_id=project_id,
        dataset_id=dataset_id,
        membership=membership,
        db=db,
    )

    try:
        file_path = _resolve_file(data.file_path)
        dataframe = _load_dataframe(file_path)

        if "price" in dataframe.columns and "close" not in dataframe.columns:
            dataframe = dataframe.rename(
                columns={
                    "price": "close",
                }
            )

        if "timestamp" not in dataframe.columns:
            raise ValueError(
                "Required column 'timestamp' is missing."
            )

        if "symbol" not in dataframe.columns:
            raise ValueError(
                "Required column 'symbol' is missing."
            )

        dataframe["timestamp"] = pd.to_datetime(
            dataframe["timestamp"],
            errors="coerce",
            utc=True,
        )

        if dataframe["timestamp"].isna().any():
            raise ValueError(
                "Timestamp column contains invalid or null values."
            )

        dataframe["symbol"] = (
            dataframe["symbol"]
            .astype(str)
            .str.strip()
        )

        dataframe = (
            dataframe
            .sort_values(["symbol", "timestamp"])
            .reset_index(drop=True)
        )

        result = VisualizationService().build(
            dataframe=dataframe,
            symbols=data.symbols,
            chart_type=data.chart_type,
            periods_per_year=data.periods_per_year,
        )

        return result

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
