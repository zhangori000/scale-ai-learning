/**
 * Ticketmaster Edge Bouncer (CDN Edge Worker)
 * Deployed globally to Cloudflare/AWS Edge nodes.
 * 
 * This worker intercepts all /poll-queue requests.
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const eventId = url.searchParams.get("event_id");

    // 1. Parse the User's JWT Token from the Authorization header.
    // The token contains the 'joined_at' timestamp signed by our Ingress API.
    const authHeader = request.headers.get("Authorization");
    if (!authHeader) {
      return new Response("Unauthorized", { status: 401 });
    }

    const token = decodeAndVerifyJWT(authHeader); // Simulation
    const userJoinedAt = token.joined_at;

    /**
     * 2. READ FROM CDN KV STORE
     * This is the 'Global Threshold' pushed by the Gatekeeper.
     * Every Edge Node has a local, cached copy of this KV.
     * Propagation time: ~5-10 seconds globally.
     */
    const admittedThreshold = await env.TICKET_KV.get(`threshold:${eventId}`);

    // 3. THE BOUNCER LOGIC
    // If user's join time is LESS THAN OR EQUAL TO threshold, they are in!
    if (userJoinedAt <= parseFloat(admittedThreshold)) {
      return Response.json({
        status: "GRANTED",
        redirect_url: `/seat-selection?token=${authHeader}`,
        message: "It's your turn! Go grab those seats."
      });
    }

    // 4. STILL WAITING
    // We return a lightweight JSON. No database or origin server touched.
    return Response.json({
      status: "WAITING",
      position_estimate: calculateEstimate(userJoinedAt, admittedThreshold),
      poll_interval_ms: 5000,
      message: "Please stay on this page. You are in the virtual queue."
    });
  }
};

function calculateEstimate(userTime, threshold) {
  // Simple linear math to give the user a 'feeling' of progress.
  const diff = userTime - threshold;
  return Math.floor(diff / 1000000); // Mocking milliseconds estimate
}
