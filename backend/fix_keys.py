#!/usr/bin/env python3
"""
Script pentru curățarea cheilor API invalide din baza de date.
Rulează pe VPS: python3 fix_keys.py
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    print("=== Verificare și curățare chei API ===\n")
    
    db = AsyncIOMotorClient("mongodb://localhost:27017")["seo_saas"]
    
    # 1. Arată starea curentă
    print("1. Stare curentă:")
    async for doc in db.user_api_keys.find({}, {"_id": 0}):
        user_id = doc.get("user_id", "?")
        print(f"\n   User: {user_id[:12]}...")
        
        for field in ["openai_key", "gemini_key", "resend_key", "pexels_key"]:
            val = doc.get(field, "")
            if not val:
                status = "(gol)"
            elif val.startswith("gAAAAAB"):
                status = f"INVALID - criptat vechi ({val[:15]}...)"
            elif val.startswith("sk-"):
                status = f"OK - OpenAI ({val[:10]}...)"
            elif val.startswith("re_"):
                status = f"OK - Resend ({val[:10]}...)"
            else:
                status = f"??? ({val[:15]}...)"
            print(f"     {field}: {status}")
    
    # 2. Curăță cheile invalide
    print("\n\n2. Curățare chei invalide (gAAAAAB...):")
    
    for field in ["openai_key", "gemini_key", "resend_key", "sendgrid_key", "pexels_key"]:
        result = await db.user_api_keys.update_many(
            {field: {"$regex": "^gAAAAAB"}},
            {"$set": {field: ""}}
        )
        if result.modified_count > 0:
            print(f"   ✓ Curățat {result.modified_count} {field} invalid(e)")
    
    # 3. Verifică din nou
    print("\n3. Stare după curățare:")
    async for doc in db.user_api_keys.find({}, {"_id": 0}):
        user_id = doc.get("user_id", "?")
        has_keys = []
        for field in ["openai_key", "gemini_key", "resend_key", "pexels_key"]:
            if doc.get(field):
                has_keys.append(field.replace("_key", ""))
        
        if has_keys:
            print(f"   User {user_id[:12]}...: {', '.join(has_keys)}")
        else:
            print(f"   User {user_id[:12]}...: (nicio cheie configurată)")
    
    print("\n=== GATA! ===")
    print("Utilizatorii trebuie acum să re-introducă cheile API din aplicație.")

if __name__ == "__main__":
    asyncio.run(main())
