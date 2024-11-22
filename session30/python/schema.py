from pydantic import BaseModel, Field
from typing import List, Optional

class Country(BaseModel):
    name: str

class IncorporatedIn(BaseModel):
    country: Country
    state: str

class Party(BaseModel):
    name: str
    role: str
    incorporated_in: IncorporatedIn

class GovernedByLaw(BaseModel):
    country: Country
    state: str

class Excerpt(BaseModel):
    text: str

class Clause(BaseModel):
    name: str
    clause_type: str
    excerpts: List[Excerpt]

class Agreement(BaseModel):
    agreement_type: str
    contract_id: int
    effective_date: str
    expiration_date: str
    renewal_term: str
    name: str

class Document(BaseModel):
    agreement: Agreement
    parties: List[Party]
    governed_by_law: GovernedByLaw
    clauses: List[Clause]
