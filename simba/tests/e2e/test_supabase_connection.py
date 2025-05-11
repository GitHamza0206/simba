import pytest
from simba.auth.supabase_client import SupabaseClientSingleton

@pytest.mark.e2e
def test_supabase_connection():
    """
    E2E: Test that Supabase connection is working and can list rows from a real table.
    """
    client = SupabaseClientSingleton.get_instance()
    # Replace 'documents' with a real table name in your Supabase project
    result = client.table('documents').select('*').limit(1).execute()
    assert result.data is not None
    assert isinstance(result.data, list)
    print("Supabase documents:", result.data) 