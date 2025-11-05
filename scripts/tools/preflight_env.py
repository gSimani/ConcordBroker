"""
Preflight environment check.

Validates presence of critical environment variables and prints a concise report.
Safe for local and CI usage (does not print secret values, only presence).
"""

import os


def check(var: str) -> bool:
    return bool(os.getenv(var))


def main() -> None:
    vars_required = [
        # Supabase
        "SUPABASE_URL",
        # Accept either service role (backend) or anon (frontend use)
    ]
    vars_optional = [
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_ANON_KEY",
        "NEXT_PUBLIC_SUPABASE_URL",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY",
        "VITE_SUPABASE_URL",
        "VITE_SUPABASE_ANON_KEY",
        # Observability
        "SENTRY_DSN",
    ]

    print("Preflight Environment Check")
    print("=" * 28)

    ok = True
    for v in vars_required:
        present = check(v)
        print(f"{v:28} : {'OK' if present else 'MISSING'}")
        ok = ok and present

    print("-" * 28)
    for v in vars_optional:
        present = check(v)
        print(f"{v:28} : {'set' if present else 'unset'}")

    # Extra guidance
    if not os.getenv("SUPABASE_SERVICE_ROLE_KEY") and not os.getenv("SUPABASE_ANON_KEY"):
        print("\nNote: Neither SUPABASE_SERVICE_ROLE_KEY nor SUPABASE_ANON_KEY is set.")
        print("- Backend scripts should use the service role key.")
        print("- Frontend apps must only use the anon key.")

    print("\nStatus:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()

