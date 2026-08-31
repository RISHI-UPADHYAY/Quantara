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
)
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

    path = _resolve_file(data.file_path)
    dataframe = _load_dataframe(path)

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
            asset_symbol=data.asset_symbol,
            benchmark_symbol=data.benchmark_symbol,
        )

    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
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