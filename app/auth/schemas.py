from sqlmodel import SQLModel

class LoginRequest(SQLModel):
    email: str
    password: str

    model_config = {
        "json_schema_extra":{
            "examples":[
                {
                    "email":"grebnevdanil60@gmail.com",
                    "password":"htczte2101"
                }
            ]
        }
    }

class TokenResponse(SQLModel):
    access_token: str
    token_type: str = 'bearer'