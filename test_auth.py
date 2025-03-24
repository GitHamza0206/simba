from supabase import create_client


supabase = create_client(
    supabase_url="http://localhost:8000",
    supabase_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.ewogICJyb2xlIjogImFub24iLAogICJpc3MiOiAic3VwYWJhc2UiLAogICJpYXQiOiAxNzQyNzc0NDAwLAogICJleHAiOiAxOTAwNTM3MjAwCn0.-C9-Rfj2hDpEJQE6O77C9UEQCsNqcaDmeJd-1AErvyE"
)



supabase.auth.sign_up(
    credentials={
        "email": "admin4@admin.com",
        "password": "hamza123"
        
    }
)

print(supabase.auth.get_user())
