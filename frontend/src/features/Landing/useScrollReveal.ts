import { useEffect } from "react";

export default function useScrollReveal() {
    useEffect(() => {
        const elements = document.querySelectorAll<HTMLElement>("[data-reveal]");

        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            elements.forEach((element) => {
                element.classList.add("is-visible");
            });
            return;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    const element = entry.target as HTMLElement;

                    if (entry.isIntersecting) {
                        element.classList.add("is-visible");
                    } else {
                        element.classList.remove("is-visible");
                    }
                });
            },
            {
                threshold: 0.12,
                rootMargin: "0px 0px -45px 0px",
            },
        );

        elements.forEach((element) => observer.observe(element));

        return () => observer.disconnect();
    }, []);
}