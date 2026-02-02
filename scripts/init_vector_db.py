#!/usr/bin/env python3
"""
Vector database initialization script for the agri-civic intelligence platform.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.vector_db_factory import get_vector_db
from app.config import get_settings


# Sample agricultural knowledge documents for initialization
SAMPLE_DOCUMENTS = [
    {
        "content": "Wheat is a cereal grain that is grown in temperate climates worldwide. It requires well-drained soil with pH between 6.0-7.5. Optimal temperature for wheat growth is 15-20°C during vegetative growth and 20-25°C during grain filling.",
        "metadata": {
            "source": "Agricultural Guidelines",
            "crop": "wheat",
            "category": "cultivation",
            "language": "en",
        },
        "id": "wheat_cultivation_001",
    },
    {
        "content": "Rice blast disease is caused by the fungus Magnaporthe oryzae. Symptoms include diamond-shaped lesions on leaves with gray centers and brown borders. Treatment includes application of tricyclazole or propiconazole fungicides.",
        "metadata": {
            "source": "Plant Disease Manual",
            "crop": "rice",
            "category": "disease_management",
            "language": "en",
        },
        "id": "rice_blast_001",
    },
    {
        "content": "Cotton bollworm (Helicoverpa armigera) is a major pest of cotton. Early detection is crucial. Use pheromone traps for monitoring. Treatment includes application of Bt cotton varieties or targeted insecticides like emamectin benzoate.",
        "metadata": {
            "source": "Pest Management Guide",
            "crop": "cotton",
            "category": "pest_management",
            "language": "en",
        },
        "id": "cotton_bollworm_001",
    },
    {
        "content": "Pradhan Mantri Fasal Bima Yojana (PMFBY) provides crop insurance coverage to farmers. It covers pre-sowing to post-harvest losses due to natural calamities, pests, and diseases. Premium rates are 2% for Kharif crops and 1.5% for Rabi crops.",
        "metadata": {
            "source": "Government Schemes",
            "category": "insurance",
            "scheme_type": "crop_insurance",
            "language": "en",
        },
        "id": "pmfby_001",
    },
    {
        "content": "Soil Health Card Scheme provides soil health information to farmers including nutrient status and recommendations for appropriate dosage of nutrients. Cards are issued every 2 years and include pH, organic carbon, and NPK levels.",
        "metadata": {
            "source": "Government Schemes",
            "category": "soil_health",
            "scheme_type": "advisory",
            "language": "en",
        },
        "id": "soil_health_card_001",
    },
    {
        "content": "Minimum Support Price (MSP) for wheat in 2024-25 is ₹2,275 per quintal. MSP ensures farmers get fair prices for their produce. Government procures crops at MSP through Food Corporation of India (FCI) and state agencies.",
        "metadata": {
            "source": "MSP Guidelines",
            "crop": "wheat",
            "category": "pricing",
            "year": "2024-25",
            "language": "en",
        },
        "id": "msp_wheat_2024",
    },
]

# Government scheme documents
GOVERNMENT_SCHEMES = [
    {
        "content": "PM-KISAN scheme provides income support of ₹6,000 per year to small and marginal farmers. Amount is transferred in three equal installments of ₹2,000 each. Eligible farmers must have cultivable land up to 2 hectares.",
        "metadata": {
            "source": "PM-KISAN Guidelines",
            "category": "income_support",
            "scheme_type": "direct_benefit_transfer",
            "eligibility": "small_marginal_farmers",
            "language": "en",
        },
        "id": "pm_kisan_001",
    },
    {
        "content": "Kisan Credit Card (KCC) provides farmers with timely access to credit for agricultural needs. Interest rate is 7% per annum with 3% interest subvention. Covers crop loans, post-harvest expenses, and maintenance of farm assets.",
        "metadata": {
            "source": "KCC Guidelines",
            "category": "credit",
            "scheme_type": "agricultural_credit",
            "interest_rate": "7%",
            "language": "en",
        },
        "id": "kcc_001",
    },
    {
        "content": "National Agriculture Market (e-NAM) is an online trading platform for agricultural commodities. Farmers can sell directly to buyers across India. Provides transparent price discovery and reduces transaction costs.",
        "metadata": {
            "source": "e-NAM Guidelines",
            "category": "marketing",
            "scheme_type": "digital_platform",
            "language": "en",
        },
        "id": "enam_001",
    },
]

# Market intelligence data
MARKET_INTELLIGENCE = [
    {
        "content": "Wheat prices in North India are expected to remain stable due to good harvest. Current average price is ₹2,200-2,300 per quintal. Demand from flour mills is steady. Export opportunities exist for high-quality wheat.",
        "metadata": {
            "source": "Market Intelligence Report",
            "crop": "wheat",
            "region": "North India",
            "category": "price_forecast",
            "language": "en",
        },
        "id": "wheat_market_001",
    },
    {
        "content": "Cotton prices showing upward trend due to strong export demand. Current prices range from ₹5,800-6,200 per quintal. Quality cotton (28-30 mm staple) commanding premium prices. Storage in proper conditions recommended.",
        "metadata": {
            "source": "Market Intelligence Report",
            "crop": "cotton",
            "category": "price_trend",
            "quality_factor": "staple_length",
            "language": "en",
        },
        "id": "cotton_market_001",
    },
]


async def initialize_vector_collections():
    """Initialize vector database collections with sample data."""

    settings = get_settings()
    print(f"🚀 Initializing vector database collections...")

    try:
        # Get vector database instance
        vector_db = get_vector_db()

        # Initialize collections
        collections_to_create = [
            "agricultural_knowledge",
            "government_schemes",
            "market_intelligence",
            "crop_diseases",
            "pest_management",
        ]

        for collection_name in collections_to_create:
            collection = vector_db.get_or_create_collection(collection_name)
            print(f"✅ Collection '{collection_name}' initialized")

        # Add sample agricultural knowledge
        if SAMPLE_DOCUMENTS:
            documents = [doc["content"] for doc in SAMPLE_DOCUMENTS]
            metadatas = [doc["metadata"] for doc in SAMPLE_DOCUMENTS]
            ids = [doc["id"] for doc in SAMPLE_DOCUMENTS]

            vector_db.add_documents("agricultural_knowledge", documents, metadatas, ids)
            print(f"✅ Added {len(SAMPLE_DOCUMENTS)} agricultural knowledge documents")

        # Add government schemes
        if GOVERNMENT_SCHEMES:
            documents = [doc["content"] for doc in GOVERNMENT_SCHEMES]
            metadatas = [doc["metadata"] for doc in GOVERNMENT_SCHEMES]
            ids = [doc["id"] for doc in GOVERNMENT_SCHEMES]

            vector_db.add_documents("government_schemes", documents, metadatas, ids)
            print(f"✅ Added {len(GOVERNMENT_SCHEMES)} government scheme documents")

        # Add market intelligence
        if MARKET_INTELLIGENCE:
            documents = [doc["content"] for doc in MARKET_INTELLIGENCE]
            metadatas = [doc["metadata"] for doc in MARKET_INTELLIGENCE]
            ids = [doc["id"] for doc in MARKET_INTELLIGENCE]

            vector_db.add_documents("market_intelligence", documents, metadatas, ids)
            print(f"✅ Added {len(MARKET_INTELLIGENCE)} market intelligence documents")

        # Display collection statistics
        print("\n📊 Collection Statistics:")
        for collection_name in collections_to_create:
            info = vector_db.get_collection_info(collection_name)
            print(f"   - {collection_name}: {info['count']} documents")

        print("\n🎉 Vector database initialization completed successfully!")

    except Exception as e:
        print(f"❌ Error initializing vector database: {e}")
        raise


async def reset_vector_collections():
    """Reset all vector database collections."""

    print("🧹 Resetting vector database collections...")

    try:
        # Get vector database instance
        vector_db = get_vector_db()

        collections_to_reset = [
            "agricultural_knowledge",
            "government_schemes",
            "market_intelligence",
            "crop_diseases",
            "pest_management",
        ]

        for collection_name in collections_to_reset:
            vector_db.reset_collection(collection_name)
            print(f"🗑️  Reset collection '{collection_name}'")

        print("✅ All vector collections reset successfully!")

    except Exception as e:
        print(f"❌ Error resetting vector collections: {e}")
        raise


async def test_vector_operations():
    """Test basic vector database operations."""

    print("🧪 Testing vector database operations...")

    try:
        # Get vector database instance
        vector_db = get_vector_db()

        # Test query
        test_query = "What is the treatment for rice blast disease?"
        results = vector_db.query_documents(
            "agricultural_knowledge", test_query, n_results=2
        )

        print(
            f"✅ Query test successful - found {len(results['documents'][0])} results"
        )

        # Test government scheme query
        scheme_query = "What schemes provide financial support to farmers?"
        scheme_results = vector_db.query_documents(
            "government_schemes", scheme_query, n_results=2
        )

        print(
            f"✅ Scheme query test successful - found {len(scheme_results['documents'][0])} results"
        )

        # Test market intelligence query
        market_query = "What are the current wheat prices?"
        market_results = vector_db.query_documents(
            "market_intelligence", market_query, n_results=2
        )

        print(
            f"✅ Market query test successful - found {len(market_results['documents'][0])} results"
        )

        print("🎉 All vector database operations tested successfully!")

    except Exception as e:
        print(f"❌ Error testing vector operations: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Vector database initialization script"
    )
    parser.add_argument(
        "--reset", action="store_true", help="Reset all vector collections"
    )
    parser.add_argument(
        "--test", action="store_true", help="Test vector database operations"
    )

    args = parser.parse_args()

    async def main():
        try:
            if args.reset:
                await reset_vector_collections()
                await initialize_vector_collections()
            elif args.test:
                await test_vector_operations()
            else:
                await initialize_vector_collections()
        except Exception as e:
            print(f"Script failed: {e}")
            sys.exit(1)

    asyncio.run(main())
