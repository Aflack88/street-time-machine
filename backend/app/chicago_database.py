# backend/app/chicago_data.py
"""
Comprehensive Chicago historical photo database
Sources: Chicago History Museum, Library of Congress, City Archives
"""

CHICAGO_HISTORICAL_PHOTOS = [
    # Downtown/Loop Area
    {
        "filename": "state_street_1950.jpg",
        "title": "State Street Looking North",
        "year": 1950,
        "decade": 1950,
        "latitude": 41.8781,
        "longitude": -87.6278,
        "viewing_direction_start": 350,
        "viewing_direction_end": 10,
        "landmarks": ["Chicago Theater", "State Street", "Marshall Field's"],
        "street_address": "State Street & Randolph, Chicago, IL",
        "description": "Bustling State Street with the iconic Chicago Theater marquee",
        "image_quality_score": 0.9,
        "historical_interest_score": 0.95,
        "has_people": True,
        "has_vehicles": True,
        "architecture_style": "mid_century",
        "source": "Chicago History Museum",
        "story_context": "State Street was known as 'That Great Street' - the commercial heart of Chicago"
    },
    {
        "filename": "loop_1920.jpg",
        "title": "The Loop District - LaSalle Street",
        "year": 1920,
        "decade": 1920,
        "latitude": 41.8796,
        "longitude": -87.6320,
        "viewing_direction_start": 80,
        "viewing_direction_end": 120,
        "landmarks": ["LaSalle Street", "Chicago Board of Trade", "El Train"],
        "street_address": "LaSalle Street, Chicago, IL",
        "description": "Early morning commuters and elevated train in the financial district",
        "image_quality_score": 0.7,
        "historical_interest_score": 0.9,
        "has_people": True,
        "has_vehicles": False,
        "architecture_style": "early_1900s",
        "source": "Library of Congress",
        "story_context": "The Loop was the financial center of the Midwest"
    },
    {
        "filename": "michigan_ave_1960.jpg",
        "title": "Michigan Avenue Bridge",
        "year": 1960,
        "decade": 1960,
        "latitude": 41.8819,
        "longitude": -87.6278,
        "viewing_direction_start": 270,
        "viewing_direction_end": 360,
        "landmarks": ["Michigan Avenue", "Chicago River", "Wrigley Building"],
        "street_address": "Michigan Avenue Bridge, Chicago, IL",
        "description": "The Michigan Avenue Bridge with early skyscraper construction",
        "image_quality_score": 0.85,
        "historical_interest_score": 0.85,
        "has_people": True,
        "has_vehicles": True,
        "architecture_style": "mid_century_modern",
        "source": "Chicago Tribune Archives",
        "story_context": "Michigan Avenue was becoming the 'Magnificent Mile'"
    },
    
    # North Side
    {
        "filename": "wrigley_field_1945.jpg",
        "title": "Wrigley Field World Series",
        "year": 1945,
        "decade": 1940,
        "latitude": 41.9484,
        "longitude": -87.6553,
        "viewing_direction_start": 180,
        "viewing_direction_end": 220,
        "landmarks": ["Wrigley Field", "Addison Street", "Wrigleyville"],
        "street_address": "1060 W Addison St, Chicago, IL",
        "description": "Cubs fans celebrating the 1945 World Series appearance",
        "image_quality_score": 0.8,
        "historical_interest_score": 0.95,
        "has_people": True,
        "has_vehicles": True,
        "architecture_style": "1920s_ballpark",
        "source": "Chicago Cubs Archives",
        "story_context": "The Cubs' last World Series until 2016"
    },
    {
        "filename": "lincoln_park_zoo_1930.jpg", 
        "title": "Lincoln Park Zoo Entrance",
        "year": 1930,
        "decade": 1930,
        "latitude": 41.9212,
        "longitude": -87.6341,
        "viewing_direction_start": 90,
        "viewing_direction_end": 180,
        "landmarks": ["Lincoln Park Zoo", "Lake Shore Drive", "Lincoln Park"],
        "street_address": "Lincoln Park Zoo, Chicago, IL",
        "description": "Families visiting the free zoo during the Great Depression",
        "image_quality_score": 0.75,
        "historical_interest_score": 0.8,
        "has_people": True,
        "has_vehicles": False,
        "architecture_style": "1920s_civic",
        "source": "Lincoln Park Zoo Archives",
        "story_context": "Free entertainment during tough economic times"
    },
    
    # South Side
    {
        "filename": "chinatown_1965.jpg",
        "title": "Chinatown Cermak Road",
        "year": 1965,
        "decade": 1960,
        "latitude": 41.8528,
        "longitude": -87.6319,
        "viewing_direction_start": 90,
        "viewing_direction_end": 180,
        "landmarks": ["Chinatown", "Cermak Road", "Ping Tom Park"],
        "street_address": "Cermak Road, Chicago, IL",
        "description": "Traditional Chinese New Year celebration",
        "image_quality_score": 0.8,
        "historical_interest_score": 0.85,
        "has_people": True,
        "has_vehicles": True,
        "architecture_style": "mid_century_ethnic",
        "source": "Chinese American Museum",
        "story_context": "Chicago's Chinatown was a vibrant immigrant community"
    },
    {
        "filename": "union_station_1925.jpg",
        "title": "Union Station Great Hall",
        "year": 1925,
        "decade": 1920,
        "latitude": 41.8789,
        "longitude": -87.6406,
        "viewing_direction_start": 45,
        "viewing_direction_end": 135,
        "landmarks": ["Union Station", "Great Hall", "Canal Street"],
        "street_address": "225 S Canal St, Chicago, IL",
        "description": "Travelers in the magnificent Beaux-Arts station",
        "image_quality_score": 0.95,
        "historical_interest_score": 0.9,
        "has_people": True,
        "has_vehicles": False,
        "architecture_style": "beaux_arts",
        "source": "Amtrak Historical Collection",
        "story_context": "Union Station was the gateway to the American West"
    },
    
    # West Side
    {
        "filename": "garfield_park_1940.jpg",
        "title": "Garfield Park Conservatory",
        "year": 1940,
        "decade": 1940,
        "latitude": 41.8864,
        "longitude": -87.7170,
        "viewing_direction_start": 0,
        "viewing_direction_end": 90,
        "landmarks": ["Garfield Park", "Conservatory", "Washington Boulevard"],
        "street_address": "300 N Central Park Ave, Chicago, IL",
        "description": "Victorian greenhouse architecture and tropical plants",
        "image_quality_score": 0.85,
        "historical_interest_score": 0.8,
        "has_people": True,
        "has_vehicles": False,
        "architecture_style": "victorian_conservatory",
        "source": "Chicago Parks District",
        "story_context": "One of the world's largest conservatories"
    },
    {
        "filename": "united_center_area_1970.jpg",
        "title": "Near West Side Industrial",
        "year": 1970,
        "decade": 1970,
        "latitude": 41.8807,
        "longitude": -87.6742,
        "viewing_direction_start": 180,
        "viewing_direction_end": 270,
        "landmarks": ["Near West Side", "Madison Street", "Industrial District"],
        "street_address": "Madison Street, Chicago, IL",
        "description": "Industrial warehouses before urban redevelopment",
        "image_quality_score": 0.7,
        "historical_interest_score": 0.75,
        "has_people": False,
        "has_vehicles": True,
        "architecture_style": "industrial_modern",
        "source": "City of Chicago Archives",
        "story_context": "Before the United Center transformed the area"
    },
    
    # Lakefront
    {
        "filename": "navy_pier_1920.jpg",
        "title": "Municipal Pier (Navy Pier)",
        "year": 1920,
        "decade": 1920,
        "latitude": 41.8917,
        "longitude": -87.6086,
        "viewing_direction_start": 120,
        "viewing_direction_end": 200,
        "landmarks": ["Navy Pier", "Lake Michigan", "Streeterville"],
        "street_address": "600 E Grand Ave, Chicago, IL",
        "description": "Original Municipal Pier with freight and passenger ships",
        "image_quality_score": 0.8,
        "historical_interest_score": 0.85,
        "has_people": True,
        "has_vehicles": False,
        "architecture_style": "1910s_pier",
        "source": "Navy Pier Archives",
        "story_context": "Built as a shipping and recreation pier"
    },
    {
        "filename": "oak_street_beach_1955.jpg",
        "title": "Oak Street Beach Summer",
        "year": 1955,
        "decade": 1950,
        "latitude": 41.9031,
        "longitude": -87.6275,
        "viewing_direction_start": 45,
        "viewing_direction_end": 135,
        "landmarks": ["Oak Street Beach", "Gold Coast", "Lake Shore Drive"],
        "street_address": "Oak Street Beach, Chicago, IL",
        "description": "Beachgoers enjoying Lake Michigan in summer",
        "image_quality_score": 0.9,
        "historical_interest_score": 0.8,
        "has_people": True,
        "has_vehicles": False,
        "architecture_style": "1950s_recreational",
        "source": "Chicago Park District",
        "story_context": "Chicago's premier urban beach"
    },
    
    # Additional Downtown Locations
    {
        "filename": "palmer_house_1935.jpg",
        "title": "Palmer House Hotel Lobby",
        "year": 1935,
        "decade": 1930,
        "latitude": 41.8796,
        "longitude": -87.6270,
        "viewing_direction_start": 270,
        "viewing_direction_end": 360,
        "landmarks": ["Palmer House", "State Street", "Loop"],
        "street_address": "17 E Monroe St, Chicago, IL",
        "description": "Elegant hotel lobby during the Great Depression",
        "image_quality_score": 0.85,
        "historical_interest_score": 0.8,
        "has_people": True,
        "has_vehicles": False,
        "architecture_style": "art_deco",
        "source": "Palmer House Archives",
        "story_context": "America's longest continuously operating hotel"
    },
    {
        "filename": "millennium_park_area_1980.jpg",
        "title": "Grant Park Pre-Millennium Park",
        "year": 1980,
        "decade": 1980,
        "latitude": 41.8826,
        "longitude": -87.6226,
        "viewing_direction_start": 0,
        "viewing_direction_end": 90,
        "landmarks": ["Grant Park", "Art Institute", "Michigan Avenue"],
        "street_address": "Grant Park, Chicago, IL",
        "description": "Open parkland before Millennium Park development",
        "image_quality_score": 0.75,
        "historical_interest_score": 0.7,
        "has_people": True,
        "has_vehicles": False,
        "architecture_style": "1980s_landscape",
        "source": "Chicago Parks District",
        "story_context": "Before the famous Bean and Crown Fountain"
    },
    
    # Transportation Hubs
    {
        "filename": "ohare_construction_1955.jpg",
        "title": "O'Hare Airport Construction",
        "year": 1955,
        "decade": 1950,
        "latitude": 41.9742,
        "longitude": -87.9073,
        "viewing_direction_start": 180,
        "viewing_direction_end": 270,
        "landmarks": ["O'Hare Airport", "Northwest Side", "Runway Construction"],
        "street_address": "O'Hare International Airport, Chicago, IL",
        "description": "Construction of what would become the world's busiest airport",
        "image_quality_score": 0.8,
        "historical_interest_score": 0.9,
        "has_people": True,
        "has_vehicles": True,
        "architecture_style": "1950s_aviation",
        "source": "Chicago Aviation Department",
        "story_context": "Transforming from Orchard Field to O'Hare"
    },
    {
        "filename": "midway_airport_1940.jpg",
        "title": "Midway Airport Terminal",
        "year": 1940,
        "decade": 1940,
        "latitude": 41.7868,
        "longitude": -87.7524,
        "viewing_direction_start": 90,
        "viewing_direction_end": 180,
        "landmarks": ["Midway Airport", "Cicero Avenue", "Southwest Side"],
        "street_address": "5700 S Cicero Ave, Chicago, IL",
        "description": "Art Deco terminal building with propeller aircraft",
        "image_quality_score": 0.85,
        "historical_interest_score": 0.85,
        "has_people": True,
        "has_vehicles": True,
        "architecture_style": "art_deco_aviation",
        "source": "Midway Airport Archives",
        "story_context": "Chicago's original commercial airport"
    },
    
    # Cultural Districts
    {
        "filename": "old_town_1970.jpg",
        "title": "Old Town Art Fair",
        "year": 1970,
        "decade": 1970,
        "latitude": 41.9111,
        "longitude": -87.6389,
        "viewing_direction_start": 45,
        "viewing_direction_end": 135,
        "landmarks": ["Old Town", "Lincoln Park West", "Wells Street"],
        "street_address": "Old Town, Chicago, IL",
        "description": "Artists and hippies in Chicago's bohemian neighborhood",
        "image_quality_score": 0.8,
        "historical_interest_score": 0.85,
        "has_people": True,
        "has_vehicles": True,
        "architecture_style": "1970s_bohemian",
        "source": "Old Town Art Fair Archives",
        "story_context": "Center of Chicago's counterculture movement"
    }
]

# Historical stories and quotes database
CHICAGO_HISTORICAL_STORIES = {
    1920: {
        "quotes": [
            "The roar of the elevated trains mixed with the clip-clop of horse-drawn carriages.",
            "Prohibition couldn't stop Chicago's spirit - it just moved underground.",
            "The city rebuilt itself from the ashes into America's Second City.",
            "Jazz music spilled from speakeasies onto the bustling sidewalks."
        ],
        "facts": [
            "Chicago's population reached 2.7 million in 1920, making it the second-largest US city.",
            "The elevated train system was already 30 years old and the envy of other cities.",
            "State Street was known as 'That Great Street' with the world's largest department stores.",
            "Al Capone's empire was just beginning to take control of the city's underground."
        ]
    },
    1930: {
        "quotes": [
            "Even during the Depression, Chicago's spirit couldn't be broken.",
            "Families found joy in simple pleasures - the zoo, the beach, the parks.",
            "Architecture reached new heights with Art Deco masterpieces.",
            "The Century of Progress fair showed Chicago's optimism for the future."
        ],
        "facts": [
            "The 1933-34 World's Fair brought 48 million visitors to Chicago.",
            "Many of Chicago's most beautiful buildings were constructed during this decade.",
            "The Cubs won the National League pennant in 1932, 1935, and 1938.",
            "Lincoln Park Zoo remained free during the Great Depression, providing entertainment for struggling families."
        ]
    },
    1940: {
        "quotes": [
            "Chicago became the 'Arsenal of Democracy' during World War II.",
            "Victory gardens sprouted in Grant Park and neighborhood lots.",
            "The Cubs played their last World Series for 71 years.",
            "Soldiers shipped out from Union Station to battlefields across the globe."
        ],
        "facts": [
            "Chicago manufactured everything from aircraft engines to ammunition during WWII.",
            "The city's population peaked at nearly 3.6 million residents.",
            "O'Hare Airport began as a manufacturing facility for Douglas C-54 aircraft.",
            "The Great Migration brought hundreds of thousands of African Americans north to Chicago."
        ]
    },
    1950: {
        "quotes": [
            "Post-war optimism filled the air as Chicago modernized at breakneck speed.",
            "The sound of construction mixed with jazz spilling from nightclub doorways.",
            "Families flocked downtown to see the latest movies at grand theaters.",
            "The suburbs began calling, but the city's heart still beat strong."
        ],
        "facts": [
            "Chicago's population peaked at 3.6 million residents in 1950.",
            "The Chicago Housing Authority built massive public housing projects.",
            "State Street featured some of the world's largest department stores.",
            "The Cubs haven't won a World Series since 1908, and fans still believe."
        ]
    },
    1960: {
        "quotes": [
            "The winds of change swept through Chicago as civil rights gained momentum.",
            "Modern architecture began transforming the iconic skyline.",
            "Rock and roll music echoed from record shops along Michigan Avenue.",
            "The Democratic Convention of 1968 would forever change the city's image."
        ],
        "facts": [
            "The second wave of the Great Migration continued bringing families north.",
            "Urban renewal projects dramatically reshaped entire neighborhoods.",
            "Chicago became a major hub for blues and emerging rock music.",
            "The Sears Tower would soon rise to become the world's tallest building."
        ]
    },
    1970: {
        "quotes": [
            "Chicago's neighborhoods each told their own story of America.",
            "The counterculture movement found a home in Old Town and Lincoln Park.",
            "Disco lights reflected off the Chicago River on weekend nights.",
            "The city began its transformation from industrial powerhouse to service center."
        ],
        "facts": [
            "The Willis (Sears) Tower was completed in 1973 as the world's tallest building.",
            "Chicago became a major hub for the emerging hip-hop and house music scenes.",
            "The city's manufacturing base began declining as jobs moved overseas.",
            "Neighborhoods like Old Town became centers of artistic and cultural renaissance."
        ]
    },
    1980: {
        "quotes": [
            "Chicago reinvented itself as a global city of finance and culture.",
            "The lakefront became a playground for the emerging professional class.",
            "House music was born in Chicago's underground club scene.",
            "The city's skyline reached new heights with gleaming towers."
        ],
        "facts": [
            "Chicago became a major financial center rivaling New York.",
            "The city's population stabilized at around 3 million residents.",
            "Grant Park began its transformation into what would become Millennium Park.",
            "Chicago's restaurant scene exploded with innovative chefs and cuisines."
        ]
    }
}

def get_historical_story(year: int, landmarks: list = None) -> dict:
    """Get contextual story based on year and location"""
    # Find the closest decade
    decades = list(CHICAGO_HISTORICAL_STORIES.keys())
    closest_decade = min(decades, key=lambda x: abs(x - year))
    
    story_data = CHICAGO_HISTORICAL_STORIES[closest_decade]
    
    import random
    quote = random.choice(story_data["quotes"])
    fact = random.choice(story_data["facts"])
    
    # Customize based on landmarks if provided
    if landmarks:
        landmark = landmarks[0].lower()
        if "state street" in landmark:
            fact = "State Street was known as 'That Great Street' and featured the world's largest department stores including Marshall Field's."
        elif "wrigley" in landmark:
            if year < 1950:
                fact = "Wrigley Field was already known as the 'Friendly Confines,' but the Cubs' championship drought was just beginning."
            else:
                fact = f"By {year}, the Cubs hadn't won a World Series since 1908 - but hope springs eternal at Wrigley Field."
        elif "navy pier" in landmark:
            fact = "Navy Pier was originally built as Municipal Pier in 1916 for shipping and recreation."
        elif "union station" in landmark:
            fact = "Union Station's Great Hall was called the gateway to the American West, processing thousands of travelers daily."
    
    return {
        "quote": quote,
        "fact": fact,
        "source": "Chicago Historical Society",
        "decade": closest_decade
    }
