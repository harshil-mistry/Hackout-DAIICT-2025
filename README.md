# CoastalGuard AI 🌊

**An AI-Powered Monitoring and Early Warning System for Coastal Resilience.**

CoastalGuard AI transforms real-time coastal data into actionable, life-saving insights. It's a proactive shield for our vulnerable coastlines, moving beyond simple data display to offer predictive analysis and a robust, multi-channel alerting system for authorities.

![CoastalGuard AI Dashboard](https://i.ibb.co/L5fN834/Screenshot-2024-05-18-at-3-11-20-PM.png)

---

 ## The Experience: What It Feels Like

When an official visits the CoastalGuard AI dashboard, they're not just looking at a website; they're stepping into a **live command center**.

Imagine viewing your entire coastline on an interactive map, with weather and sea conditions streaming in from dozens of sources in real-time. But you're not just seeing raw numbers. You're seeing **AI-generated insights** appear alongside the data, flagging anomalies and predicting potential threats hours or even days in advance. A sudden change in wave patterns? The AI suggests monitoring for a potential riptide. Worsening cyclonic conditions? The AI recommends a specific alert level and provides a clear course of action.

This is the feeling of **foresight and control**. It's the confidence that comes from having a tireless AI analyst watching over the coast 24/7, ensuring that when a critical situation develops, you are the first to know and the best prepared to act.

---

## Key Features

* 🌐 **Live Geospatial Dashboard:** A clean, intuitive interface visualizing real-time weather data, sea conditions, and community reports on an interactive map.

* 🤖 **AI-Powered Predictive Insights:** At its core, the system uses the Google Gemini LLM to analyze complex data streams. It doesn't just show you the weather; it tells you what the weather *means* for your specific region, providing predictive alerts and actionable recommendations.

* 🚨 **Critical Alert System (SMS & Email):** When conditions become critical, the system automatically dispatches alerts to the appropriate authorities via both **Email** (for detailed reports and maps) and **SMS** (for immediate warnings). This dual-channel approach ensures that crucial messages get through, **even if internet connectivity is down** for the recipient.

* 👥 **Community-Driven Reporting:** A built-in forum empowers local residents and fisherfolk to act as the eyes and ears on the ground. They can report incidents like pollution or illegal activity, with their reports appearing instantly on the official's dashboard for verification and action.

---

## Screenshots (Progress made  so far...)

<table>
  <tr>
    <td align="center"><strong>Community Reporting Forum</strong></td>
    <td align="center"><strong>AI Alert Panel</strong></td>
  </tr>
  <tr>
    <td><img src="https://i.ibb.co/L5fN834/Screenshot-2024-05-18-at-3-11-20-PM.png" alt="Community Forum Screenshot" width="400"></td>
    <td><img src="https://i.ibb.co/L5fN834/Screenshot-2024-05-18-at-3-11-20-PM.png" alt="AI Alert Panel Screenshot" width="400"></td>
  </tr>
</table>

---

## How It Works

The system operates on a simple yet powerful data flow:

1.  **Data Ingestion:** A background process continuously fetches the latest weather and oceanographic data from multiple public APIs.
2.  **AI Analysis:** This data is formatted into a detailed prompt and sent to the **Google Gemini LLM**, which acts as our core analytical engine.
3.  **Actionable Insights:** Gemini returns a structured JSON object containing the current threat level, a concise reason for its assessment, and a recommended course of action.
4.  **Instant Dispatch & Storage:** If a threat is detected, the system immediately triggers the Twilio API to send SMS and email alerts. The alert is also saved to a Firestore database.
5.  **Visualization:** The Flask backend renders the dashboard, pulling the latest live data, AI insights, and community reports to provide a complete, up-to-the-minute view for the user.



---

## Tech Stack

* **Backend & Rendering:** Python (Flask) & Jinja2
* **Styling:** Tailwind CSS
* **Database:** SQLite
* **AI Core:** Google Gemini API
* **Alerting:** Twilio API (SMS & Email)
* **Data Source:** OpenWeatherMap API

---

## Getting Started

To get a local copy up and running, follow these simple steps.

**Prerequisites:**
* Python 3.8+

**Installation:**

1.  **Clone the repo:**
    ```
    git clone [https://github.com/your_username/CoastalGuard-AI.git](https://github.com/your_username/CoastalGuard-AI.git)
    cd CoastalGuard-AI
    ```
2.  **Install Python packages:**
    ```sh
    pip install -r requirements.txt
    ```
3.  **Install JS packages and build CSS:**
    ```sh
    npm install
    npm run build:css
    ```
4.  **Set up your environment variables:**
    * Create a `.env` file in the root directory.
    * Add your API keys

5.  **Run the application:**
    ```sh
    python app.py
    ```
