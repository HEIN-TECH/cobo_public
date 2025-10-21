from dataclasses import dataclass
from typing import Optional


# Constants

class Status:
    OK = 0
    INVALID_REQUEST = 10
    INVALID_TOKEN = 20
    INTERNAL_ERROR = 30


@dataclass
class PackageDataClaim:
    """JWT claims with package data and standard JWT claims"""

    package_data: Optional[str] = None
    aud: Optional[str] = None  # Audience
    exp: Optional[int] = None  # Expiration Time
    jti: Optional[str] = None  # JWT ID
    iat: Optional[int] = None  # Issued At
    iss: Optional[str] = None  # Issuer
    nbf: Optional[int] = None  # Not Before
    sub: Optional[str] = None  # Subject

    def to_dict(self):
        claims = {
            "package_data": self.package_data,
            "aud": self.aud,
            "exp": self.exp,
            "jti": self.jti,
            "iat": self.iat,
            "iss": self.iss,
            "nbf": self.nbf,
            "sub": self.sub,
        }
        return {k: v for k, v in claims.items() if v is not None}
