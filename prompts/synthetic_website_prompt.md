# Synthetic Website Generation Prompt

## Prompt

You are generating synthetic websites for an ad auction simulation.

The goal is to create realistic website profiles that could exist in the real world.

Each website must represent a site primarily focused on one of the following categories:


-   Fashion
-   Automotive
-   Real Estate

The generated websites will serve as an environment to simulate the ads bidding, display and consumer feedback. 

The output must follow EXACTLY this JSON schema:

```json
{
  "name": string,
  "page_context": string (Title + Context),
  "ad_placement": "banner" | "sidebar" | "interstitial",
  "category": string (choose from Fashion | Automotive | Real Estate)
}
```

### Rules for Generation

#### Category Distribution

Generate roughly equal websites for each category:
- ~3 Fashion
- ~3 Automotive
- ~4 Real Estate

#### Website Name Rules

- Names must be realistic and diverse, similar to actual US-based websites (e.g., "Vogue", "Car and Driver", "Zillow", "Fashionista", "MotorTrend", "Realtor.com").
- Avoid duplicates; each name must be unique.

#### Page Context Rules

- Each website must have a realistic page context, such as "article about summer fashion trends", "review of new electric cars", "guide to buying a home".
- Page context must logically align with the main category.
- It's individual orientation of the content, agnostic to potential ads. 

#### Ad Placement Rules

- Ad placement must be one of: "banner", "sidebar", "interstitial".
- Distribute placements evenly across websites.

#### Category Rules

- Category must be one of: "fashion", "automotive", "real estate".
- Must match the main focus of the website and page context.

#### Diversity

- Generate diverse website names, page contexts, and ad placements.
- Ensure a mix of well-known and lesser-known site names.

#### Output Rules

- Generate **10 websites**
- Return **ONLY valid JSON**
- No explanations
- Return a **JSON array**

