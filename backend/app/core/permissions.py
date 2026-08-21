ROLE_USER = "user"
ROLE_ANALYST = "analyst"
ROLE_RECRUITER = "recruiter"
ROLE_ADMIN = "admin"
ROLE_SUPER_ADMIN = "super_admin"

MANAGEABLE_ROLES = {
    ROLE_ADMIN: {
        ROLE_USER,
        ROLE_ANALYST,
        ROLE_RECRUITER,
    },

    ROLE_SUPER_ADMIN: {
        ROLE_USER,
        ROLE_ANALYST,
        ROLE_RECRUITER,
        ROLE_ADMIN,
    },
}

def can_manage_role(requester_role: str, target_role: str) -> bool:
    allowed_roles = MANAGEABLE_ROLES.get(requester_role, set())

    return target_role in allowed_roles