
import sys
sys.path.insert(0, "/app")

from datetime import timedelta
from app.security import create_access_token

# Create token with 10 year expiration
token = create_access_token(
    data={"sub": "nextjs-client", "type": "service", "role": "application"},
    expires_delta=timedelta(days=3650)
)
# Write directly to file
with open("/app/token.result", "w") as f:
    f.write(token)
