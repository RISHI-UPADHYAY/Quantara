import { useState } from "react";
import { useNavigate } from "react-router-dom";


type Plan = {
    id: "pilot" | "team" | "enterprise";
    name: string;
    description: string;
    features: string[];
};

const plans: Plan[] = [
    {
        id: "pilot",
        name: "Institutional Pilot",
        description: "Evaluate Quantara with a focused team.",
        features: [
            "Core financial analytics",
            "Guided pilot onboarding",
            "Defined evaluation scope",
        ],
    },
    {
        id: "team",
        name: "Team",
        description: "For firms building a shared research workflow.",
        features: [
            "Shared team workflows",
            "Organization-level access",
            "Team collaboration",
        ],
    },
    {
        id: "enterprise",
        name: "Enterprise",
        description: "For firms requiring tailored deployement and controls.",
        features: [
            "Enterprise deployement discussions",
            "Custom access requirements",
            "Dedicated onboarding planning",
        ],
    },
];


export default function SubscriptionSelection() {
    const navigate = useNavigate();
    const [selectedPlan, setSelectedPlan] = useState<Plan["id"]>("pilot");

    function continueToWorkspace() {
        sessionStorage.setItem(
            "quantara_pending_plan",
            selectedPlan,
        );

        navigate("/workspace/create");
    }

    return (
        <main className="mx-auto w-full max-w-5xl px-6 py-12">
            <header className="mb-8">
                <p className="text-sm font-medium text-blue-600">
                    QUANTARA · ORGANIZATION SETUP
                </p>

                <h1 className="mt-2 text-3xl font-semibold">
                    Choose your engagement
                </h1>

                <p className="mt-3 max-w-2xl text-gray-600">
                    Select how your firm would like to begin using
                    Quantara. You can continue to organization setup
                    after making your selection.
                </p>
            </header>

            <section className="grid gap-5 md:grid-cols-3">
                {plans.map((plan) => {
                    const selected = selectedPlan === plan.id;

                    return (
                        <button
                            key={plan.id}
                            type="button"
                            onClick={() => setSelectedPlan(plan.id)}
                            aria-pressed={selected}
                            className={`rounded-xl border p-6 text-left transition ${
                                selected
                                    ? "border-blue-600 ring-2 ring-blue-100"
                                    : "border-gray-200 hover:border-gray-400"
                            }`}
                        >
                            <span className="text-lg font-semibold">
                                {plan.name}
                            </span>

                            <p className="mt-3 text-sm text-gray-600">
                                {plan.description}
                            </p>

                            <ul className="mt-5 space-y-2 text-sm">
                                {plan.features.map((feature) => (
                                    <li key={feature}>✓ {feature}</li>
                                ))}
                            </ul>

                            <p className="mt-5 text-sm font-medium">
                                {selected ? "Selected" : "Select this option"}
                            </p>
                        </button>
                    );
                })}
            </section>

            <p className="mt-6 text-sm text-gray-500">
                This selection records your intended engagement only.
                No payment is collected, and no subscription is
                activated by this screen.
            </p>

            <div className="mt-8">
                <button
                    type="button"
                    onClick={continueToWorkspace}
                    className="rounded-lg bg-blue-600 px-5 py-3 font-medium text-white hover:bg-blue-700"
                >
                    Continue to organization setup
                </button>
            </div>
        </main>
    )
}