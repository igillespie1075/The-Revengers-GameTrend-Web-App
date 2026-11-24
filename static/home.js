// Home page: fills in the vote total and each platform's top games
// from GET /api/summary.
//
// To use it, the home page template needs:
//   <p>Total surveys: <span id="total-surveys">…</span></p>
//   <div id="platform-summary" class="results-grid"></div>
//   <script src="{{ url_for('static', filename='home.js') }}"></script>
//
// Change SUMMARY_URL to show a different category, e.g.
//   "/api/summary?category=all&limit=4"

const SUMMARY_URL = "/api/summary?category=favorite&limit=4";

async function loadHomeSummary() {
    const totalSlot = document.getElementById("total-surveys");
    const container = document.getElementById("platform-summary");

    if (!container) {
        return;
    }

    try {
        const response = await fetch(SUMMARY_URL);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Could not load the home page data");
        }

        if (totalSlot) {
            totalSlot.textContent = data.total_surveys;
        }

        container.innerHTML = "";

        for (const platform of data.platforms) {
            container.appendChild(buildPlatformCard(platform, data.title));
        }

    } catch (error) {
        container.textContent = error.message;
    }
}

// One card per platform: name, survey count and its ranked games.
// Built with textContent (not innerHTML) so game names can't inject HTML.
function buildPlatformCard(platform, categoryTitle) {
    const card = document.createElement("article");

    const heading = document.createElement("h3");
    heading.textContent = platform.platform;

    const subtitle = document.createElement("p");
    subtitle.className = "hint";
    subtitle.textContent =
        `${categoryTitle} · ${platform.surveys} ` +
        (platform.surveys === 1 ? "survey" : "surveys");

    const list = document.createElement("ol");

    for (const game of platform.top_games) {
        const item = document.createElement("li");
        item.textContent = `${game.game} — ${game.votes} votes`;
        list.appendChild(item);
    }

    if (platform.top_games.length === 0) {
        const item = document.createElement("li");
        item.textContent = "No votes yet";
        list.appendChild(item);
    }

    card.append(heading, subtitle, list);
    return card;
}

loadHomeSummary();
