"""
graph.py — Social Network Graph and Friend Recommendation Engine

This module defines:
  - The User data structure
  - The SocialGraph class (built on NetworkX)
  - The mutual-friend recommendation algorithm
  - A helper to render the graph as a PNG image
"""

import io
import networkx as nx
import matplotlib
matplotlib.use("Agg")          # Non-interactive backend — no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# ---------------------------------------------------------------------------
# Sample data — hardcoded users and friendships
# ---------------------------------------------------------------------------

# Each user has a name, age, and a list of interests
USERS = {
    "alice":   {"name": "Alice",   "age": 24, "interests": ["music", "hiking", "photography"]},
    "bob":     {"name": "Bob",     "age": 26, "interests": ["gaming", "cooking", "music"]},
    "carol":   {"name": "Carol",   "age": 23, "interests": ["reading", "yoga", "hiking"]},
    "david":   {"name": "David",   "age": 27, "interests": ["photography", "travel", "cooking"]},
    "eve":     {"name": "Eve",     "age": 25, "interests": ["gaming", "travel", "music"]},
    "frank":   {"name": "Frank",   "age": 28, "interests": ["coding", "hiking", "cooking"]},
    "grace":   {"name": "Grace",   "age": 22, "interests": ["yoga", "reading", "photography"]},
    "henry":   {"name": "Henry",   "age": 29, "interests": ["travel", "music", "coding"]},
    "iris":    {"name": "Iris",    "age": 24, "interests": ["cooking", "gaming", "yoga"]},
    "jake":    {"name": "Jake",    "age": 26, "interests": ["hiking", "coding", "travel"]},
}

# Friendship pairs (undirected — if Alice knows Bob, Bob knows Alice)
FRIENDSHIPS = [
    ("alice", "bob"),
    ("alice", "carol"),
    ("alice", "frank"),
    ("bob",   "carol"),
    ("bob",   "eve"),
    ("bob",   "henry"),
    ("carol", "grace"),
    ("carol", "david"),
    ("david", "henry"),
    ("david", "jake"),
    ("eve",   "iris"),
    ("eve",   "henry"),
    ("frank", "jake"),
    ("frank", "carol"),
    ("grace", "iris"),
    ("henry", "jake"),
    ("iris",  "jake"),
]


# ---------------------------------------------------------------------------
# SocialGraph class
# ---------------------------------------------------------------------------

class SocialGraph:
    """
    Wraps a NetworkX undirected graph to model a social network.

    Each node = a user (string key from USERS).
    Each edge = a friendship between two users.
    """

    def __init__(self):
        # Create an undirected graph
        self.graph = nx.Graph()

        # Add every user as a node, storing their profile data
        for user_id, profile in USERS.items():
            self.graph.add_node(user_id, **profile)

        # Add every friendship as an edge
        for u, v in FRIENDSHIPS:
            self.graph.add_edge(u, v)

    def get_friends(self, user_id):
        """Return the set of direct friends for a given user."""
        return set(self.graph.neighbors(user_id))

    def get_mutual_friends(self, user_a, user_b):
        """
        Return the set of users who are friends with BOTH user_a and user_b.
        These are the 'mutual friends' that make user_b a good suggestion for user_a.
        """
        friends_a = self.get_friends(user_a)
        friends_b = self.get_friends(user_b)
        return friends_a & friends_b   # set intersection

    def recommend_friends(self, user_id, top_n=5):
        """
        Suggest up to `top_n` new friends for `user_id`.

        Algorithm:
          1. Collect every user who is NOT already a direct friend (and not the user themselves).
          2. For each candidate, count how many mutual friends they share with `user_id`.
          3. Sort candidates by mutual-friend count (descending).
          4. Return the top `top_n` candidates with their mutual-friend details.
        """
        direct_friends = self.get_friends(user_id)
        # Everyone except the user themselves and their existing friends
        candidates = set(self.graph.nodes) - direct_friends - {user_id}

        recommendations = []
        for candidate in candidates:
            mutuals = self.get_mutual_friends(user_id, candidate)
            if mutuals:   # Only suggest people who share at least one mutual friend
                mutual_names = [USERS[m]["name"] for m in mutuals]
                recommendations.append({
                    "user_id":      candidate,
                    "name":         USERS[candidate]["name"],
                    "age":          USERS[candidate]["age"],
                    "interests":    USERS[candidate]["interests"],
                    "mutual_count": len(mutuals),
                    "mutual_names": mutual_names,
                })

        # Sort by most mutual friends first
        recommendations.sort(key=lambda r: r["mutual_count"], reverse=True)
        return recommendations[:top_n]

    def build_graph_image(self, selected_user=None):
        """
        Render the social network as a PNG image using Matplotlib.

        - All nodes are drawn as circles labelled with the user's first name.
        - The selected user is highlighted in a distinct colour.
        - Direct friends of the selected user are highlighted differently.
        - Returns raw PNG bytes (to be sent as an HTTP response).
        """
        fig, ax = plt.subplots(figsize=(10, 7))
        fig.patch.set_facecolor("#f8f9fa")
        ax.set_facecolor("#f8f9fa")

        # Use a spring layout so the graph spreads out nicely
        pos = nx.spring_layout(self.graph, seed=42, k=1.8)

        # --- Colour each node based on its role ---
        direct_friends = self.get_friends(selected_user) if selected_user else set()

        node_colors = []
        node_sizes  = []
        for node in self.graph.nodes:
            if node == selected_user:
                node_colors.append("#e74c3c")   # Red  — selected user
                node_sizes.append(1800)
            elif node in direct_friends:
                node_colors.append("#2ecc71")   # Green — direct friend
                node_sizes.append(1400)
            else:
                node_colors.append("#3498db")   # Blue  — everyone else
                node_sizes.append(1100)

        # --- Draw edges ---
        nx.draw_networkx_edges(
            self.graph, pos,
            ax=ax,
            edge_color="#adb5bd",
            width=1.5,
            alpha=0.7,
        )

        # --- Draw nodes ---
        nx.draw_networkx_nodes(
            self.graph, pos,
            ax=ax,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.9,
        )

        # --- Draw labels (first name only) ---
        labels = {uid: USERS[uid]["name"] for uid in self.graph.nodes}
        nx.draw_networkx_labels(
            self.graph, pos,
            labels=labels,
            ax=ax,
            font_size=9,
            font_weight="bold",
            font_color="white",
        )

        # --- Legend ---
        legend_handles = [
            mpatches.Patch(color="#e74c3c", label="Selected user"),
            mpatches.Patch(color="#2ecc71", label="Direct friends"),
            mpatches.Patch(color="#3498db", label="Other users"),
        ]
        ax.legend(handles=legend_handles, loc="upper left", fontsize=9, framealpha=0.8)

        ax.set_title("Social Network Graph", fontsize=14, fontweight="bold", pad=15)
        ax.axis("off")
        plt.tight_layout()

        # Save to an in-memory buffer and return raw bytes
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.read()
