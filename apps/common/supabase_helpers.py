"""
Supabase helper utilities for safe access patterns.

Guidelines:
- Prefer PostgREST (table endpoints + filters) for standard CRUD operations.
- For complex operations, create vetted RPCs with parameter validation and RLS.
- Avoid generic "execute_sql" RPCs that take raw SQL strings.
"""

import os
import requests
from typing import Any, Dict, Optional


class SupabaseClient:
    def __init__(self, url: Optional[str] = None, anon_key: Optional[str] = None, service_key: Optional[str] = None):
        self.url = url or os.getenv('SUPABASE_URL')
        self.anon_key = anon_key or os.getenv('SUPABASE_ANON_KEY')
        self.service_key = service_key or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        if not self.url or not (self.anon_key or self.service_key):
            raise ValueError('Supabase URL/key not configured')

    def _headers(self, use_service: bool = False) -> Dict[str, str]:
        token = self.service_key if use_service and self.service_key else self.anon_key
        return {
            'apikey': token,
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def table_select(self, table: str, params: Dict[str, Any]) -> Any:
        qs = '&'.join([f"{k}={v}" for k, v in params.items()]) if params else ''
        url = f"{self.url}/rest/v1/{table}" + (f"?{qs}" if qs else '')
        resp = requests.get(url, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def table_insert(self, table: str, rows: Any) -> Any:
        url = f"{self.url}/rest/v1/{table}"
        headers = self._headers(use_service=True)
        headers['Prefer'] = 'return=representation'
        resp = requests.post(url, json=rows, headers=headers)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def table_update(self, table: str, match: Dict[str, Any], data: Dict[str, Any]) -> Any:
        url = f"{self.url}/rest/v1/{table}"
        if match:
            qs = '&'.join([f"{k}=eq.{v}" for k, v in match.items()])
            url += f"?{qs}"
        resp = requests.patch(url, json=data, headers=self._headers(use_service=True))
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def table_delete(self, table: str, match: Dict[str, Any]) -> Any:
        url = f"{self.url}/rest/v1/{table}"
        if match:
            qs = '&'.join([f"{k}=eq.{v}" for k, v in match.items()])
            url += f"?{qs}"
        resp = requests.delete(url, headers=self._headers(use_service=True))
        resp.raise_for_status()
        return {'status': 'deleted'}

    def call_rpc(self, name: str, params: Dict[str, Any]) -> Any:
        """Call a vetted RPC.

        Do not use this for raw "execute_sql" calls.
        """
        url = f"{self.url}/rest/v1/rpc/{name}"
        resp = requests.post(url, json=params, headers=self._headers(use_service=True))
        resp.raise_for_status()
        return resp.json() if resp.content else {}

