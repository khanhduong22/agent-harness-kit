#!/usr/bin/env node

/**
 * manage_domains.mjs
 *
 * Automate Firebase Auth authorized domain management via Google Identity Platform REST API.
 * Uses native Node.js (v18+) crypto and fetch for zero-dependency OAuth2 JWT token exchange.
 */

import crypto from 'node:crypto';
import dns from 'node:dns';
import fs from 'node:fs';
import path from 'node:path';

try {
  dns.setDefaultResultOrder('ipv4first');
} catch {
  // Optional on environments without setDefaultResultOrder
}

const IS_TTY = Boolean(process.stdout.isTTY) && !process.env.NO_COLOR;
const colors = {
  reset: IS_TTY ? '\x1b[0m' : '',
  bold: IS_TTY ? '\x1b[1m' : '',
  dim: IS_TTY ? '\x1b[2m' : '',
  green: IS_TTY ? '\x1b[32m' : '',
  yellow: IS_TTY ? '\x1b[33m' : '',
  blue: IS_TTY ? '\x1b[34m' : '',
  magenta: IS_TTY ? '\x1b[35m' : '',
  cyan: IS_TTY ? '\x1b[36m' : '',
  red: IS_TTY ? '\x1b[31m' : '',
};

function printUsage() {
  console.log(`
${colors.bold}${colors.cyan}Firebase Authorized Domains Manager${colors.reset}
Automate Firebase Auth OAuth authorized domains via Google Identity Platform REST API.

${colors.bold}USAGE:${colors.reset}
  node manage_domains.mjs <command> [domains...] [options]

${colors.bold}COMMANDS:${colors.reset}
  ${colors.green}list${colors.reset}                             List all currently authorized domains
  ${colors.green}add${colors.reset} <domain1> [domain2...]      Add one or more domains to the authorized list
  ${colors.green}remove${colors.reset} <domain1> [domain2...]   Remove one or more domains from the authorized list
  ${colors.green}help${colors.reset}                             Show this help message

${colors.bold}OPTIONS:${colors.reset}
  ${colors.yellow}--key, -k <path>${colors.reset}               Path to serviceAccountKey.json (or env FIREBASE_SERVICE_ACCOUNT_KEY)
  ${colors.yellow}--project, -p <id>${colors.reset}             Override Google Cloud / Firebase Project ID
  ${colors.yellow}--json${colors.reset}                          Output machine-readable JSON
  ${colors.yellow}--help, -h${colors.reset}                      Show help

${colors.bold}EXAMPLES:${colors.reset}
  node manage_domains.mjs list --key ./serviceAccountKey.json
  node manage_domains.mjs add example.com www.example.com --key ./serviceAccountKey.json
  node manage_domains.mjs add preview-pr-12.domain.app --key ./serviceAccountKey.json
  node manage_domains.mjs remove obsolete.domain.app --key ./serviceAccountKey.json
`);
}

function cleanDomain(input) {
  if (!input) return '';
  let d = input.trim();
  // Strip protocol
  d = d.replace(/^https?:\/\//i, '');
  // Strip trailing slashes and paths
  d = d.split('/')[0];
  // Strip port (e.g., localhost:3000 -> localhost)
  d = d.split(':')[0];
  return d.toLowerCase();
}

function parseArgs(args) {
  const parsed = {
    command: '',
    domains: [],
    keyPath: process.env.FIREBASE_SERVICE_ACCOUNT_KEY || process.env.GOOGLE_APPLICATION_CREDENTIALS || '',
    projectId: process.env.FIREBASE_PROJECT_ID || '',
    json: false,
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--key' || arg === '-k') {
      parsed.keyPath = args[++i];
    } else if (arg.startsWith('--key=')) {
      parsed.keyPath = arg.slice(6);
    } else if (arg === '--project' || arg === '-p') {
      parsed.projectId = args[++i];
    } else if (arg.startsWith('--project=')) {
      parsed.projectId = arg.slice(10);
    } else if (arg === '--json') {
      parsed.json = true;
    } else if (arg === '--help' || arg === '-h') {
      parsed.command = 'help';
    } else if (!parsed.command) {
      parsed.command = arg.toLowerCase();
    } else {
      const parts = arg.split(',').map(cleanDomain).filter(Boolean);
      parsed.domains.push(...parts);
    }
  }

  return parsed;
}

function loadServiceAccount(keyPath) {
  if (!keyPath) {
    throw new Error(
      'Missing service account key path. Specify via --key <path> or env FIREBASE_SERVICE_ACCOUNT_KEY.'
    );
  }

  const resolved = path.resolve(process.cwd(), keyPath);
  if (!fs.existsSync(resolved)) {
    throw new Error(`Service account file not found at: ${resolved}`);
  }

  let raw;
  try {
    raw = fs.readFileSync(resolved, 'utf8');
  } catch (err) {
    throw new Error(`Failed to read service account file: ${err.message}`);
  }

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (err) {
    throw new Error(`Invalid JSON in service account file: ${err.message}`);
  }

  if (!parsed.client_email || !parsed.private_key) {
    throw new Error(
      'Service account JSON missing required fields (client_email, private_key).'
    );
  }

  return parsed;
}

function base64url(input) {
  return Buffer.from(input).toString('base64url');
}

function createSignedJwt(serviceAccount, scope) {
  const now = Math.floor(Date.now() / 1000);
  const header = {
    alg: 'RS256',
    typ: 'JWT',
  };
  const claimSet = {
    iss: serviceAccount.client_email,
    scope,
    aud: 'https://oauth2.googleapis.com/token',
    exp: now + 3600,
    iat: now,
  };

  const encodedHeader = base64url(JSON.stringify(header));
  const encodedClaimSet = base64url(JSON.stringify(claimSet));
  const signInput = `${encodedHeader}.${encodedClaimSet}`;

  const signer = crypto.createSign('RSA-SHA256');
  signer.update(signInput);
  const signature = signer.sign(serviceAccount.private_key, 'base64url');

  return `${signInput}.${signature}`;
}

async function fetchWithRetry(url, options, retries = 3, timeoutMs = 15000) {
  let lastError;
  for (let attempt = 1; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      clearTimeout(timer);
      return response;
    } catch (err) {
      clearTimeout(timer);
      lastError = err;
      if (attempt < retries) {
        const delay = 1000 * Math.pow(2, attempt - 1);
        await new Promise((r) => setTimeout(r, delay));
      }
    }
  }
  throw lastError;
}

async function getAccessToken(serviceAccount) {
  const scope = 'https://www.googleapis.com/auth/cloud-platform';
  const jwt = createSignedJwt(serviceAccount, scope);

  const res = await fetchWithRetry('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion: jwt,
    }).toString(),
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Failed to exchange JWT for OAuth2 access token (${res.status}): ${errorBody}`);
  }

  const data = await res.json();
  if (!data.access_token) {
    throw new Error('OAuth2 token endpoint returned no access_token');
  }

  return data.access_token;
}

async function getAuthorizedDomains(projectId, accessToken) {
  const url = `https://identitytoolkit.googleapis.com/admin/v2/projects/${projectId}/config`;
  const res = await fetchWithRetry(url, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      Accept: 'application/json',
    },
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Failed to fetch Firebase config (${res.status}): ${errorBody}`);
  }

  const config = await res.json();
  return Array.isArray(config.authorizedDomains) ? config.authorizedDomains : [];
}

async function updateAuthorizedDomains(projectId, accessToken, domains) {
  const url = `https://identitytoolkit.googleapis.com/admin/v2/projects/${projectId}/config?updateMask=authorizedDomains`;
  const res = await fetchWithRetry(url, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify({
      authorizedDomains: domains,
    }),
  });

  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Failed to update authorized domains (${res.status}): ${errorBody}`);
  }

  const config = await res.json();
  return Array.isArray(config.authorizedDomains) ? config.authorizedDomains : [];
}

async function main() {
  const args = process.argv.slice(2);
  const parsed = parseArgs(args);

  if (!parsed.command || parsed.command === 'help') {
    printUsage();
    process.exit(0);
  }

  if (!['list', 'add', 'remove'].includes(parsed.command)) {
    console.error(`${colors.red}Unknown command:${colors.reset} "${parsed.command}"`);
    printUsage();
    process.exit(1);
  }

  const sa = loadServiceAccount(parsed.keyPath);
  const projectId = parsed.projectId || sa.project_id;

  if (!projectId) {
    throw new Error('Project ID could not be determined from service account or --project option.');
  }

  if (!parsed.json) {
    console.log(`${colors.cyan}Authenticating with Google Identity Platform for project:${colors.reset} ${colors.bold}${projectId}${colors.reset}`);
  }

  const accessToken = await getAccessToken(sa);

  if (parsed.command === 'list') {
    const domains = await getAuthorizedDomains(projectId, accessToken);

    if (parsed.json) {
      console.log(JSON.stringify({
        success: true,
        projectId,
        count: domains.length,
        authorizedDomains: domains,
      }, null, 2));
      return;
    }

    console.log(`\n${colors.bold}${colors.green}✓ Authorized Domains for Firebase Project:${colors.reset} ${colors.cyan}${projectId}${colors.reset}`);
    console.log(`${colors.dim}Total: ${domains.length} domains${colors.reset}\n`);
    domains.forEach((d, idx) => {
      console.log(`  ${colors.dim}${String(idx + 1).padStart(2, ' ')}.${colors.reset} ${colors.bold}${d}${colors.reset}`);
    });
    console.log('');
    return;
  }

  if (parsed.command === 'add') {
    if (parsed.domains.length === 0) {
      throw new Error('Please specify at least one domain to add. Example: add example.com www.example.com');
    }

    const currentDomains = await getAuthorizedDomains(projectId, accessToken);
    const currentSet = new Set(currentDomains);
    const toAdd = parsed.domains.filter((d) => !currentSet.has(d));
    const alreadyPresent = parsed.domains.filter((d) => currentSet.has(d));

    if (toAdd.length === 0) {
      if (parsed.json) {
        console.log(JSON.stringify({
          success: true,
          projectId,
          changed: false,
          message: 'All specified domains are already authorized.',
          authorizedDomains: currentDomains,
        }, null, 2));
        return;
      }

      console.log(`\n${colors.yellow}ℹ All specified domains are already authorized:${colors.reset}`);
      alreadyPresent.forEach((d) => console.log(`  - ${d} (already authorized)`));
      console.log(`${colors.dim}No changes required.${colors.reset}\n`);
      return;
    }

    const updatedList = [...currentDomains, ...toAdd];
    const result = await updateAuthorizedDomains(projectId, accessToken, updatedList);

    if (parsed.json) {
      console.log(JSON.stringify({
        success: true,
        projectId,
        changed: true,
        added: toAdd,
        alreadyAuthorized: alreadyPresent,
        authorizedDomains: result,
      }, null, 2));
      return;
    }

    console.log(`\n${colors.bold}${colors.green}✓ Successfully added ${toAdd.length} domain(s) to ${projectId}:${colors.reset}`);
    toAdd.forEach((d) => console.log(`  ${colors.green}+ ${d}${colors.reset}`));
    if (alreadyPresent.length > 0) {
      console.log(`${colors.dim}Already authorized: ${alreadyPresent.join(', ')}${colors.reset}`);
    }

    console.log(`\n${colors.bold}Total authorized domains (${result.length}):${colors.reset}`);
    result.forEach((d, idx) => {
      const isNew = toAdd.includes(d);
      const marker = isNew ? ` ${colors.green}(new)${colors.reset}` : '';
      console.log(`  ${colors.dim}${String(idx + 1).padStart(2, ' ')}.${colors.reset} ${d}${marker}`);
    });
    console.log('');
    return;
  }

  if (parsed.command === 'remove') {
    if (parsed.domains.length === 0) {
      throw new Error('Please specify at least one domain to remove. Example: remove old.example.com');
    }

    const currentDomains = await getAuthorizedDomains(projectId, accessToken);
    const targets = new Set(parsed.domains);
    const toRemove = currentDomains.filter((d) => targets.has(d));

    if (toRemove.length === 0) {
      if (parsed.json) {
        console.log(JSON.stringify({
          success: true,
          projectId,
          changed: false,
          message: 'None of the specified domains were found in the authorized list.',
          authorizedDomains: currentDomains,
        }, null, 2));
        return;
      }

      console.log(`\n${colors.yellow}ℹ None of the specified domains were in the authorized list:${colors.reset}`);
      parsed.domains.forEach((d) => console.log(`  - ${d} (not found)`));
      console.log(`${colors.dim}No changes made.${colors.reset}\n`);
      return;
    }

    const updatedList = currentDomains.filter((d) => !targets.has(d));
    const result = await updateAuthorizedDomains(projectId, accessToken, updatedList);

    if (parsed.json) {
      console.log(JSON.stringify({
        success: true,
        projectId,
        changed: true,
        removed: toRemove,
        authorizedDomains: result,
      }, null, 2));
      return;
    }

    console.log(`\n${colors.bold}${colors.green}✓ Successfully removed ${toRemove.length} domain(s) from ${projectId}:${colors.reset}`);
    toRemove.forEach((d) => console.log(`  ${colors.red}- ${d}${colors.reset}`));

    console.log(`\n${colors.bold}Remaining authorized domains (${result.length}):${colors.reset}`);
    result.forEach((d, idx) => {
      console.log(`  ${colors.dim}${String(idx + 1).padStart(2, ' ')}.${colors.reset} ${d}`);
    });
    console.log('');
  }
}

main().catch((err) => {
  console.error(`\n${colors.red}${colors.bold}Error:${colors.reset} ${err.message}\n`);
  process.exit(1);
});
