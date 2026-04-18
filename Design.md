# Design System Specification: The Architectural Intelligence
 
## 1. Overview & Creative North Star: "The Digital Curator"
This design system is built to transform the chaotic process of high-volume intern hiring into a streamlined, high-fidelity experience. Our Creative North Star is **The Digital Curator**. Unlike standard SaaS platforms that feel like "software," this system should feel like a premium editorial tool—an authoritative, high-density environment that favors precision over flash.
 
We break the "template" look by rejecting the rigid, boxed-in layouts of the early web. Instead, we utilize **Intentional Asymmetry** and **Tonal Depth**. By removing 1px borders and heavy outlines, we allow the data to breathe, using the hierarchy of light and surface to guide the eye. It is an atmosphere of transparency, efficiency, and quiet technological power.
 
---
 
## 2. Color & Surface Philosophy
The palette is rooted in deep, authoritative navies (`primary_container: #063342`) and vibrant, surgical accents (`secondary: #006a62`). 
 
### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders for sectioning or containment. Boundaries must be defined solely through background color shifts or subtle tonal transitions.
*   *Implementation:* Use `surface_container_low` for the main body and `surface_container_lowest` for a card. The 2-4% shift in luminance is sufficient to define the edge without visual clutter.
 
### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers, similar to stacked sheets of frosted glass.
*   **Layer 0 (Base):** `surface` (#f9f9ff)
*   **Layer 1 (Main Content Area):** `surface_container_low` (#eff3ff)
*   **Layer 2 (Interactive Modules):** `surface_container_lowest` (#ffffff)
*   **Layer 3 (Active/Pop-over):** `surface_bright` with Glassmorphism.
 
### The Glass & Gradient Rule
To move beyond a "standard" UI, floating elements (modals, dropdowns, hovering navigation) must use **Glassmorphism**. Apply a semi-transparent `surface_variant` with a `backdrop-blur` of 12px–20px. 
*   **Signature Texture:** Primary CTAs should not be flat. Apply a subtle linear gradient from `primary` (#001d28) to `primary_container` (#063342) at a 135-degree angle to provide a "machined" professional finish.
 
---
 
## 3. Typography: Editorial Authority
We utilize **Inter** across the entire system. The goal is a high-density, data-rich environment that remains legible under intense scrutiny.
 
*   **Display (lg/md):** Reserved for high-level dashboard metrics (e.g., "Total Candidates: 1,240"). Use a tight tracking (-0.02em) for a more modern, "Linear-esque" feel.
*   **Headline & Title:** Used for navigation headers and card titles. Use `on_surface` (#121c2a) to maintain a strong contrast against the light surfaces.
*   **Body (md/sm):** This is the workhorse of the system. In data tables, use `body-sm` with a slightly increased line-height (1.5) to maintain readability in high-density views.
*   **Label (md/sm):** These should be styled in `on_tertiary_container` (#8c97a9) to clearly distinguish metadata from primary content.
 
---
 
## 4. Elevation & Depth: Tonal Layering
We do not use shadows to simulate height; we use **lightness**.
 
*   **The Layering Principle:** Place a `surface_container_lowest` card on a `surface_container_low` section. This creates a "Soft Lift."
*   **Ambient Shadows:** For floating elements like tooltips or modals, use a "Ghost Shadow."
    *   *Shadow Specs:* `0px 12px 32px rgba(18, 28, 42, 0.06)`. The shadow color is a tinted version of `on_surface`, not a neutral grey.
*   **The Ghost Border Fallback:** If a border is required for accessibility (e.g., in Dark Mode), use the `outline_variant` token at **15% opacity**. Never use a 100% opaque border.
 
---
 
## 5. Components: The Primitive Set
 
### Buttons & CTAs
*   **Primary:** Gradient of `primary` to `primary_container`. Text: `on_primary`. Radius: `md` (0.375rem).
*   **Secondary (Ghost):** No background, `outline_variant` (15% opacity) border. Text: `primary`.
*   **Tertiary:** Transparent background, `on_surface_variant` text. High-density padding (8px 12px).
 
### Sophisticated Data Tables
*   **Rules:** Forbid horizontal and vertical divider lines.
*   **Separation:** Use alternating row fills of `surface_container_low` and `surface_container_lowest`.
*   **Headers:** Use `label-md` in all-caps with 0.05em letter spacing for an architectural feel.
 
### Progress Trackers (The Pipeline)
*   Instead of a line-and-dot tracker, use a "Segmented Bar." 
*   **In-Progress:** `secondary` (#006a62) with a subtle pulse animation.
*   **Completed:** `secondary_container` (#6cf5e6).
*   **Empty:** `surface_variant`.
 
### Adaptive Navigation
*   **Admin/HR:** A high-density vertical sidebar using `primary_container` (#063342) as the background. Icons should be monochrome `on_primary_container` until hovered.
*   **Candidate:** A centered, "Glass" top-navigation bar to emphasize a simpler, more focused journey.
 
---
 
## 6. Do’s and Don’ts
 
### Do
*   **Do** use white space as a structural element. If two pieces of data feel cluttered, increase the gap before you consider adding a line.
*   **Do** use `secondary` (#006a62) for success states and "AI-powered" insights to associate the brand color with intelligence.
*   **Do** use `0.375rem (md)` as your base border radius for a balance of "friendly" and "precise."
 
### Don’t
*   **Don’t** use pure black (#000000) for text. Always use `on_surface` (#121c2a) to maintain a premium, ink-on-paper feel.
*   **Don’t** use standard "drop shadows" on cards. If the tonal shift between `surface` tiers isn't visible, your monitor calibration or your opacity settings are likely too high.
*   **Don’t** use high-contrast borders. A border should be felt, not seen.