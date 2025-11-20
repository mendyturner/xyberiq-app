# LiveLIVE Foundation – 12 Days of Giving Landing Page

This repository contains a single-page experience for the LiveLIVE Foundation’s “12 Days of Giving” holiday drive supporting single-parent households and military veterans. The page is fully static (`index.html`) and uses inline CSS and Google Fonts—no build step or external dependencies are required.

## Highlights
- **Logo-inspired palette** (red, black, white, gold) and a recreated wordmark lockup to match the provided artwork.
- **Hero block** with campaign metrics, primary CTA buttons linked to Stripe Checkout, and messaging for the seasonal drive.
- **Impact, schedule, and giving tiers** detailing how donations are used, the 12-day action plan, and suggested contribution levels.
- **Stripe donate buttons** (placeholder Checkout link) repeated across the page for quick conversions.
- **Responsive layout** that stacks gracefully on tablets and mobile devices.

## Usage
1. Serve `index.html` from any static host (e.g., GitHub Pages, Netlify, S3) or open it locally in a browser.
2. Replace the placeholder Stripe URL (`https://donate.stripe.com/test_dR65nZ1Gh5XW1qY7ss`) with the production Checkout link when ready.
3. (Optional) Swap the inline logo recreation with the official PNG/SVG asset by updating the header markup.

## Customization Tips
- **Copy & Dates:** Update campaign dates, metrics, or section text directly inside `index.html`.
- **Brand colors:** Adjust the CSS variables declared in the `:root` block if the palette evolves.
- **Analytics / embeds:** Add your tracking scripts or signup forms before the closing `</body>` tag.

## Preview
Simply open `index.html` in your browser to preview the full experience. No additional setup is required.
