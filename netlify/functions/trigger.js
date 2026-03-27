// Netlify serverless function — proxies workflow_dispatch to GitHub API
// Requires env var: GITHUB_PAT (token with `workflow` scope)
// and GITHUB_REPO (e.g. "GaspardCoche/agent-system")

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") {
    return { statusCode: 405, body: "Method Not Allowed" };
  }

  const pat = process.env.GITHUB_PAT;
  const repo = process.env.GITHUB_REPO || "GaspardCoche/agent-system";

  if (!pat) {
    return { statusCode: 500, body: JSON.stringify({ error: "GITHUB_PAT not configured" }) };
  }

  let body;
  try {
    body = JSON.parse(event.body);
  } catch {
    return { statusCode: 400, body: JSON.stringify({ error: "Invalid JSON" }) };
  }

  const { workflow, inputs = {} } = body;
  if (!workflow) {
    return { statusCode: 400, body: JSON.stringify({ error: "Missing workflow" }) };
  }

  const url = `https://api.github.com/repos/${repo}/actions/workflows/${workflow}/dispatches`;

  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${pat}`,
      Accept: "application/vnd.github+json",
      "Content-Type": "application/json",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: JSON.stringify({ ref: "main", inputs }),
  });

  if (res.status === 204) {
    return { statusCode: 200, body: JSON.stringify({ ok: true }) };
  }

  const text = await res.text();
  return {
    statusCode: res.status,
    body: JSON.stringify({ error: text }),
  };
};
