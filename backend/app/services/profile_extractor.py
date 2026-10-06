import re
from typing import Any


def extract_profile_updates(
    transcript: str,
    language: str | None = None,
) -> dict[str, Any]:
    """
    Extract basic farmer-profile information from a transcript.

    This is the initial rule-based version.
    Later, Sarvam LLM will handle more flexible language
    understanding.
    """

    text = transcript.strip()
    text_lower = text.lower()

    updates: dict[str, Any] = {}

    # ---------------------------------------------------------
    # 1. CROP
    # ---------------------------------------------------------

    crop_keywords = {
        "cotton": "cotton",
        "wheat": "wheat",
        "rice": "rice",
        "paddy": "rice",
        "soybean": "soybean",
        "soyabean": "soybean",
        "sugarcane": "sugarcane",
        "maize": "maize",
        "corn": "maize",
        "onion": "onion",
        "potato": "potato",
        "tomato": "tomato",
        "grape": "grape",
        "grapes": "grape",

        # Hindi
        "कपास": "cotton",
        "गेहूं": "wheat",
        "गेहूँ": "wheat",
        "धान": "rice",
        "चावल": "rice",
        "सोयाबीन": "soybean",
        "गन्ना": "sugarcane",
        "मक्का": "maize",
        "प्याज": "onion",
        "आलू": "potato",
        "टमाटर": "tomato",

        # Marathi
        "कापूस": "cotton",
        "गहू": "wheat",
        "भात": "rice",
        "सोयाबीन": "soybean",
        "ऊस": "sugarcane",
        "मका": "maize",
        "कांदा": "onion",
        "बटाटा": "potato",
        "टोमॅटो": "tomato",
    }

    for keyword, crop_name in crop_keywords.items():
        if keyword in text_lower or keyword in text:
            updates["crop"] = crop_name
            break

    # ---------------------------------------------------------
    # 2. LAND AREA
    # ---------------------------------------------------------

    # Examples:
    # "I have 3 acres"
    # "I have 3 acre land"
    # "3 acres of land"
    # "मेरे पास 3 एकड़ जमीन है"
    # "मेरे पास तीन एकड़ जमीन है"

    number_match = re.search(
        r"(\d+(?:\.\d+)?)\s*"
        r"(acres?|acre|hectares?|hectare|"
        r"एकड़|एकर|हेक्टेयर|"
        r"एकर|एकरांची)",
        text_lower,
    )

    if number_match:
        area = float(number_match.group(1))
        unit = number_match.group(2)

        if any(word in unit for word in ["acre", "एकड़", "एकर"]):
            normalized_unit = "acre"
        elif any(word in unit for word in ["hectare", "हेक्टेयर"]):
            normalized_unit = "hectare"
        else:
            normalized_unit = unit

        updates["land_area"] = area
        updates["land_unit"] = normalized_unit

    # Common English phrasing:
    # "my farm is 3 acres"
    # "my land is 5 acres"

    if "land_area" not in updates:
        english_land_match = re.search(
            r"(?:land|farm)\s+(?:is|has|of)\s+"
            r"(\d+(?:\.\d+)?)\s*(acre|acres|hectare|hectares)",
            text_lower,
        )

        if english_land_match:
            updates["land_area"] = float(
                english_land_match.group(1)
            )

            unit = english_land_match.group(2)

            updates["land_unit"] = (
                "acre"
                if "acre" in unit
                else "hectare"
            )

    # ---------------------------------------------------------
    # 3. PREVIOUS CROP LOSS
    # ---------------------------------------------------------

    loss_phrases = [
        "crop was damaged",
        "crop got damaged",
        "crop was destroyed",
        "crop got destroyed",
        "crop loss",
        "lost my crop",
        "crop failed",
        "heavy rain damaged",
        "heavy rainfall damaged",

        # Hindi
        "फसल खराब",
        "फसल बर्बाद",
        "फसल नष्ट",
        "फसल का नुकसान",
        "फसल खराब हो गई",

        # Marathi
        "पीक खराब",
        "पीकाचे नुकसान",
        "पिकाचे नुकसान",
        "पीक नष्ट",
        "पीकाचे नुकसान झाले",
    ]

    if any(phrase in text_lower or phrase in text for phrase in loss_phrases):
        updates["previous_crop_loss"] = True

    # ---------------------------------------------------------
    # 4. LOSS REASON
    # ---------------------------------------------------------

    loss_reasons = {
        "heavy rain": "heavy_rain",
        "heavy rainfall": "heavy_rain",
        "excess rain": "heavy_rain",
        "flood": "flood",
        "flooding": "flood",
        "drought": "drought",
        "no rain": "drought",
        "hail": "hailstorm",
        "hailstorm": "hailstorm",
        "pest": "pest",
        "pests": "pest",
        "disease": "crop_disease",
        "strong wind": "strong_wind",
        "cyclone": "cyclone",

        # Hindi
        "भारी बारिश": "heavy_rain",
        "बारिश": "heavy_rain",
        "बाढ़": "flood",
        "सूखा": "drought",
        "ओलावृष्टि": "hailstorm",
        "कीट": "pest",
        "बीमारी": "crop_disease",

        # Marathi
        "मुसळधार पाऊस": "heavy_rain",
        "अतिवृष्टी": "heavy_rain",
        "पूर": "flood",
        "दुष्काळ": "drought",
        "गारपीट": "hailstorm",
        "कीड": "pest",
        "रोग": "crop_disease",
    }

    for phrase, reason in loss_reasons.items():
        if phrase in text_lower or phrase in text:
            updates["loss_reason"] = reason
            updates["previous_crop_loss"] = True
            break

    # ---------------------------------------------------------
    # 5. PREVIOUS INSURANCE
    # ---------------------------------------------------------

    previous_insurance_phrases = [
        "i had insurance",
        "i have insurance",
        "i took insurance",
        "i had crop insurance",
        "i previously had insurance",
        "already insured",

        # Hindi
        "मैंने बीमा लिया",
        "मेरे पास बीमा था",
        "फसल बीमा लिया",

        # Marathi
        "मी विमा घेतला",
        "माझा पीक विमा होता",
        "पीक विमा घेतला",
    ]

    no_insurance_phrases = [
        "never had insurance",
        "never took insurance",
        "i don't have insurance",
        "i do not have insurance",
        "no insurance",

        # Hindi
        "मैंने कभी बीमा नहीं लिया",
        "मेरे पास बीमा नहीं है",

        # Marathi
        "मी कधीही विमा घेतला नाही",
        "माझ्याकडे विमा नाही",
    ]

    if any(
        phrase in text_lower or phrase in text
        for phrase in previous_insurance_phrases
    ):
        updates["previous_insurance"] = True

    elif any(
        phrase in text_lower or phrase in text
        for phrase in no_insurance_phrases
    ):
        updates["previous_insurance"] = False

    # ---------------------------------------------------------
    # 6. INSURANCE INTEREST
    # ---------------------------------------------------------

    positive_interest = [
        "i want insurance",
        "i want crop insurance",
        "i am interested in insurance",
        "i would like insurance",
        "yes i want insurance",

        # Hindi
        "मुझे बीमा चाहिए",
        "मैं बीमा लेना चाहता",
        "मैं बीमा लेना चाहती",
        "मुझे फसल बीमा चाहिए",

        # Marathi
        "मला विमा हवा",
        "मला पीक विमा हवा",
        "मला विमा घ्यायचा आहे",
    ]

    negative_interest = [
        "i don't want insurance",
        "i do not want insurance",
        "not interested in insurance",
        "i am not interested",

        # Hindi
        "मुझे बीमा नहीं चाहिए",
        "मुझे बीमा नहीं लेना",

        # Marathi
        "मला विमा नको",
        "मला विमा घ्यायचा नाही",
    ]

    if any(
        phrase in text_lower or phrase in text
        for phrase in positive_interest
    ):
        updates["insurance_interest"] = "interested"

    elif any(
        phrase in text_lower or phrase in text
        for phrase in negative_interest
    ):
        updates["insurance_interest"] = "not_interested"

    return updates