import useSWR, { SWRConfiguration } from "swr";
import { API_BASE } from "./api";

/**
 * Custom SWR hook that uses the full backend API URL
 * Ensures all data fetching goes through the centralized API module
 * Pass empty string "" to disable polling
 */
export function useApi<T>(endpoint: string, options?: SWRConfiguration) {
    // Only fetch if endpoint is not empty
    const shouldFetch = endpoint.length > 0;
    const url = shouldFetch ? `${API_BASE}${endpoint}` : null;

    const fetcher = async (url: string) => {
        const res = await fetch(url);
        if (!res.ok) {
            throw new Error(`API Error: ${res.status}`);
        }
        return res.json() as Promise<T>;
    };

    return useSWR<T | null>(url, fetcher, {
        revalidateOnFocus: false,
        ...options,
    });
}

export { useApi as useSWRWithBackend };
