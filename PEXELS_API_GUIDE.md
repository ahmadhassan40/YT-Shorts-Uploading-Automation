# How to Get a Free Pexels API Key

To enable automatic topic-based video downloads, you need a Pexels API key. It's completely free!

## Steps

1.  **Go to Pexels API**: Visit [https://www.pexels.com/api/](https://www.pexels.com/api/)
2.  **Sign Up / Log In**: Create a free account if you don't have one.
3.  **Request API Key**:
    *   Click usually on "Your API Key" or "Get Started".
    *   Fill in the short form (you can say "Personal Project" or "Bot Development").
    *   It's usually approved instantly.
4.  **Copy the Key**: You will see a long string of random characters (e.g., `563492ad6f91700001000001...`).
5.  **Configure Your Bot**:
    *   Open `config/settings.yaml`.
    *   Find the `stock_videos` section.
    *   Paste your key:
        ```yaml
        stock_videos:
          provider: "pexels"
          api_key: "YOUR_COPIED_KEY_HERE"
          orientation: "portrait"
        ```

## That's it!
Your bot will now automatically search for and download high-quality vertical videos matching your script's topic!
