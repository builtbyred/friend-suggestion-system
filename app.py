"""
app.py — Main Flask Application

Routes:
  GET  /              — Home page: user selection dropdown
  POST /recommend     — Run the recommendation algorithm and display results
  GET  /graph/<user>  — Return a PNG image of the social network graph
  GET  /about         — Short explanation of how the algorithm works
"""

import os
from flask import Flask, render_template, request, redirect, url_for, Response

# Import our social-graph engine
from graph import SocialGraph, USERS

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)

# Create a single shared graph instance (it never changes at runtime)
social_graph = SocialGraph()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """
    Home page.
    Renders a dropdown listing every user so the visitor can choose
    whose friend recommendations they want to see.
    """
    # Sort users alphabetically by their display name for a tidy dropdown
    users = sorted(USERS.items(), key=lambda item: item[1]["name"])
    return render_template("index.html", users=users)


@app.route("/recommend", methods=["POST"])
def recommend():
    """
    Recommendation page.
    Reads the selected user from the form, runs the mutual-friend algorithm,
    and renders the results together with the user's profile and friend list.
    """
    selected_id = request.form.get("user_id")

    # Guard against invalid or missing input
    if not selected_id or selected_id not in USERS:
        return redirect(url_for("index"))

    profile       = USERS[selected_id]
    friends       = social_graph.get_friends(selected_id)
    # Build friendly display info for each direct friend
    friend_info   = [{"user_id": f, **USERS[f]} for f in friends]
    friend_info.sort(key=lambda u: u["name"])

    recommendations = social_graph.recommend_friends(selected_id, top_n=5)

    return render_template(
        "recommendations.html",
        selected_id     = selected_id,
        profile         = profile,
        friend_info     = friend_info,
        recommendations = recommendations,
    )


@app.route("/graph/<user_id>")
def graph_image(user_id):
    """
    Returns a PNG image of the social network with `user_id` highlighted.
    The <img> tag in recommendations.html points here.
    """
    if user_id not in USERS:
        return "User not found", 404

    png_bytes = social_graph.build_graph_image(selected_user=user_id)
    return Response(png_bytes, mimetype="image/png")


@app.route("/about")
def about():
    """Simple page explaining how the recommendation algorithm works."""
    return render_template("about.html")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Use PORT env variable if set (Replit sets it), otherwise default to 5000
    port = int(os.environ.get("PORT", 5000))
    # Only enable debug mode in development — never in production
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
