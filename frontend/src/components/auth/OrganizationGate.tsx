import React, { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { listOrganizations } from "../../services/organizationService";


interface OrganizationGateProps {
    children: React.ReactNode;
}

export default function OrganizationGate ({
    children,
}: OrganizationGateProps) {
    const [loading, setLoading] = useState(true);
    const [hasOrganization, setHasOraganization] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;

        async function checkOrganizations() {
            try {
                const organizations = await listOrganizations();

                if (!cancelled) {
                    setHasOraganization(organizations.length > 0);
                    setError(null);
                }
            } catch {
                if (!cancelled) {
                    setError("We couldn't verify your organization membership.");
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }

        void checkOrganizations();

        return () => {
            cancelled = true;
        };
    }, []);

    if (loading) {
        return (
            <div role="status">Checking your workspace...</div>
        )
    }

    if (error) {
        return (
            <div className="alert">
                <p>{error}</p>
                <button onClick={() => window.location.reload()}>
                    Retry
                </button>
            </div>
        );
    }

    if (!hasOrganization) {
        return (
            <Navigate to="/subscriptions" replace />
        )
    }

    return <>{children}</>;
}