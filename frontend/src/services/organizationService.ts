import api from "./api";

export interface Organization {
    id: string
    name: string
    slug: string
}

export interface CreateOrganizationRequest {
    name: string
    slug: string
}


export async function listOrganizations(): Promise<Organization[]> {
    const response = await api.get<Organization[]>("/organizations");
    return response.data;
}


export async function createOrganization(
    payload: CreateOrganizationRequest,
): Promise<Organization> {
    const response = await api.post<Organization>(
        "/organizations",
        payload,
    );

    return response.data;
}