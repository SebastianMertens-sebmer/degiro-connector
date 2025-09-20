scripts remove personal data move it to an .env 

move claude md /Users/sebastianmertens/Documents/GitHub/degiro-connector/custom-trading/docs/CLAUDE.md to main part - tell it to be careful cause of the mainstream i am not sure we are arealy getting commits from external


  📝 Example Request Body

  {
    "underlying_id": "331868",
    "action": "LONG",
    "min_leverage": 2.0,
    "max_leverage": 10.0,
    "limit": 10,
    "product_subtype": "MINI"
  }

  🍎 Test Product Details

  - Product ID: 331868 (Apple Inc stock)
  - Expected Results: Knockouts (Mini Long products) for Apple
  - Real Pricing: Should show live prices like €0.89 instead of fake prices

  🎯 Test Different Product Types

  1. Optionsscheine (Traditional Options):
  {"underlying_id": "331868", "product_subtype": "CALL_PUT"}

  2. Knockouts (Mini Products):
  {"underlying_id": "331868", "product_subtype": "MINI"}

  3. Faktor Certificates:
  {"underlying_id": "331868", "product_subtype": "UNLIMITED"}

  4. All Products:
  {"underlying_id": "331868", "product_subtype": "ALL"}