import pytest
from unittest.mock import MagicMock, patch

# Create a mock Supabase client
mock_supabase = MagicMock()
mock_supabase.table.return_value.select.return_value.limit.return_value.execute.return_value.data = []

@pytest.fixture(scope="session", autouse=True)
def patch_supabase_client():
    with patch('simba.auth.supabase_client.SupabaseClientSingleton.get_instance', return_value=mock_supabase), \
         patch('simba.auth.supabase_client.get_supabase_client', return_value=mock_supabase):
        yield 