import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import {
    createOrganization,
    listOrganizations,
} from "../../services/organizationService";
import { getApiErrorMessage } from "../../services/api";

const PENDING_PLAN_KEY = "quantara_pending_plan";
const SELECTED_PLAN_KEY = "quantara_selected_plan";

export default function CreateWorkspace() {
    const navigate = useNavigate();

    const [organizationName, setOrganizationName] = useState("");
    const [loading, setLoading] = useState(false);
    const [checking, setChecking] = useState(false);
    const [error, setError] = useState("");

    const selectedPlan = sessionStorage.getItem(PENDING_PLAN_KEY);

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setError("");

        const name = organizationName.trim()

        if (name.length < 2) {
            setError("Organization name must contain at least 2 characters.");
            return;
        }

        setLoading(true);

        try {
            // Avoid creating a duplicate organization if one already exists.
            setChecking(true);
            const organizations = await listOrganizations();
            setChecking(false);

            if (organizations.length > 0) {
                sessionStorage.removeItem(PENDING_PLAN_KEY);
                navigate("/dashboard", { replace: true });
                return;
            }

            const slug = name
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, "-")
                .replace(/^-+|-+$/g, "");

            if (!slug) {
                setError("Please enter an organization name using letters or numbers.");
                return;
            }

            await createOrganization({
                name,
                slug,
            });

            sessionStorage.setItem(SELECTED_PLAN_KEY, selectedPlan ?? "pilot");
            sessionStorage.removeItem(PENDING_PLAN_KEY);

            navigate ("/dashboard", { replace: true });
        } catch (err: unknown) {
            setError(
                getApiErrorMessage(
                    err,
                    "We couldn't create your organization. Please try again.",
                ),
            );
        } finally {
            setLoading(false);
            setChecking(false);
        }
    }

    if (!selectedPlan) {
        return (
            <main className="mx-auto max-w-xl px-6 py-12">
                <h1 className="text-2xl font-semibold">
                    Choose an engagement first
                </h1>
                <p className="mt-3 text-gray-600">
                    Select your Quantara engagement before creating your organization.
                </p>

                <button
                    type="button"
                    onClick={() => navigate("/subscriptions", { replace: true })}
                    className="mt-6 rounded-lg bg-blue-600 px-5 py-3 text-white"
                >
                    Choose engagement
                </button>
            </main>
        );
    }

    return (
        <main className="mx-auto w-full max-w-2xl px-6 py-12">
            <header className="mb-8">
                <p className="text-sm font-medium text-blue-600">
                    QUANTARA · ORGANIZATION SETUP
                </p>
                <h1 className="mt-2 text-3xl font-semibold">
                    Create your organization
                </h1>
                <p className="mt-3 text-gray-600">
                    Set up your firm's organization. You can add employees and configure
                    team workspaces as those features become available.
                </p>
            </header>

            <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                    <label 
                        htmlFor="organizationName"
                        className="mb-2 block text-sm font-medium"
                    >
                        Organization name
                    </label>
                    <input
                        id="organizationName"
                        name="organizationName" 
                        type="text"
                        autoComplete="organization"
                        value={organizationName}
                        onChange={(event) => setOrganizationName(event.target.value)}
                        placeholder="e.g. Example Capital"
                        required
                        minLength={2}
                        maxLength={120}
                        className="w-full rounded-lg border-gray-300 px-4 py-3 outline-none focus:border-blue-600" 
                    />
                </div>

                {error && (
                    <p role="alert" className="text-sm text-red-600">
                        {error}
                    </p>
                )}

                <button
                    type="submit"
                    disabled={loading || checking}
                    className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                    {checking
                        ? "Checking organization..."
                        : "Create organization"
                    }
                </button>
            </form>

            <p className="mt-6 text-sm text-gray-500">
                Choosing an engagement does not charge you or activate a paid
                subscription. Billing and subscription entitlements are not connected
                to this setup flow yet.
            </p>
        </main>
    )
}