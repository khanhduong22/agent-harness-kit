#!/usr/bin/env node
/**
 * fetch-slack-thread.mjs
 * 
 * Fetches an entire Slack thread or scans a Slack channel (default: #index-dev C09E30T7V7T)
 * for the latest feedback thread(s), resolves author names, downloads all attached
 * images and files, and generates a structured Markdown + JSON summary for AI agents
 * and developers.
 * 
 * Usage:
 *   # Scan latest feedback thread in #index-dev (default channel C09E30T7V7T)
 *   node fetch-slack-thread.mjs --latest
 *   node fetch-slack-thread.mjs
 * 
 *   # Fetch specific thread URL
 *   node fetch-slack-thread.mjs "https://itify-workspace.slack.com/archives/C09E30T7V7T/p1793345354377479"
 * 
 *   # Fetch specific channel & timestamp
 *   node fetch-slack-thread.mjs --channel C09E30T7V7T --ts 1793345354.377479
 * 
 *   # Scan active threads in the last 24 hours
 *   node fetch-slack-thread.mjs --hours 24
 * 
 *   # Self-test
 *   node fetch-slack-thread.mjs --test
 */

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

// ==========================================
// 1. Constants & Defaults
// ==========================================
export const DEFAULT_CHANNEL_ID = 'C09E30T7V7T'; // #index-dev
export const DEFAULT_TARGET_USER_ID = 'U09NR1YEC3Y'; // @Khánh Dương P.
export const DEFAULT_TARGET_ASSIGNEE = 'khanhduong22'; // GitHub username

// ==========================================
// 2. Secrets & Token Loader
// ==========================================
export function loadSecrets() {
  const secretsFile = process.env.AGENT_HARNESS_SECRETS || path.join(os.homedir(), '.config/agent-harness/secrets.env');
  const envVars = {};
  if (fs.existsSync(secretsFile)) {
    try {
      const content = fs.readFileSync(secretsFile, 'utf8');
      for (const line of content.split('\n')) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        const match = trimmed.match(/^(?:export\s+)?([A-Z0-9_]+)\s*=\s*(.*)$/);
        if (match) {
          let val = match[2].trim();
          if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
            val = val.slice(1, -1);
          }
          envVars[match[1]] = val;
        }
      }
    } catch (err) {
      // Ignore read errors
    }
  }
  return { secretsFile, envVars };
}

export function resolveSlackToken(explicitToken = null) {
  if (explicitToken) return { token: explicitToken, source: 'CLI argument' };

  if (process.env.SLACK_USER_TOKEN) return { token: process.env.SLACK_USER_TOKEN, source: 'process.env.SLACK_USER_TOKEN' };
  if (process.env.SLACK_BOT_TOKEN) return { token: process.env.SLACK_BOT_TOKEN, source: 'process.env.SLACK_BOT_TOKEN' };
  if (process.env.SLACK_TOKEN) return { token: process.env.SLACK_TOKEN, source: 'process.env.SLACK_TOKEN' };

  const { secretsFile, envVars } = loadSecrets();
  if (envVars.SLACK_USER_TOKEN) return { token: envVars.SLACK_USER_TOKEN, source: `${secretsFile} (SLACK_USER_TOKEN)` };
  if (envVars.SLACK_BOT_TOKEN) return { token: envVars.SLACK_BOT_TOKEN, source: `${secretsFile} (SLACK_BOT_TOKEN)` };
  if (envVars.SLACK_TOKEN) return { token: envVars.SLACK_TOKEN, source: `${secretsFile} (SLACK_TOKEN)` };

  return { token: null, source: null, secretsFile };
}

// ==========================================
// 3. URL and Timestamp Parser
// ==========================================
export function parseSlackUrlOrArgs(inputUrl, channelArg, tsArg) {
  if (channelArg && tsArg) {
    return {
      channel: channelArg.trim(),
      ts: tsArg.trim(),
      rawTs: tsArg.trim().replace('.', ''),
      originalUrl: null,
    };
  }

  if (!inputUrl) {
    throw new Error('No Slack URL or channel/ts provided.');
  }

  let parsed;
  try {
    parsed = new URL(inputUrl);
  } catch (err) {
    // If not a full URL, check if input is in format "C09E30T7V7T/p1793345354377479"
    const simpleMatch = inputUrl.match(/([A-Z0-9]+)\/p?(\d+)/i);
    if (simpleMatch) {
      const channel = simpleMatch[1];
      const raw = simpleMatch[2];
      const ts = raw.length > 6 ? `${raw.slice(0, raw.length - 6)}.${raw.slice(raw.length - 6)}` : raw;
      return { channel, ts, rawTs: raw, originalUrl: inputUrl };
    }
    throw new Error(`Invalid Slack URL or format: "${inputUrl}". Expected format: https://<workspace>.slack.com/archives/<CHANNEL>/p<TIMESTAMP>`);
  }

  // Path format: /archives/<CHANNEL_ID>/p<16_DIGITS>
  const match = parsed.pathname.match(/\/archives\/([A-Z0-9]+)\/p(\d+)/i);
  if (!match) {
    throw new Error(`Could not find channel and message timestamp in URL path: "${parsed.pathname}"`);
  }

  const channel = match[1];
  const rawTs = match[2];

  // If query parameter thread_ts is present, it explicitly points to the thread root
  const threadTsParam = parsed.searchParams.get('thread_ts');
  let ts;
  if (threadTsParam && /^\d+(\.\d+)?$/.test(threadTsParam)) {
    ts = threadTsParam;
  } else {
    // p1793345354377479 -> 1793345354.377479 (insert dot before last 6 digits)
    if (rawTs.length > 6) {
      ts = `${rawTs.slice(0, rawTs.length - 6)}.${rawTs.slice(rawTs.length - 6)}`;
    } else {
      ts = rawTs;
    }
  }

  return {
    channel,
    ts,
    rawTs,
    originalUrl: inputUrl,
  };
}

// ==========================================
// 4. Slack API Handlers
// ==========================================
export async function fetchConversationHistory(channel, token, limit = 25, oldest = null) {
  const url = new URL('https://slack.com/api/conversations.history');
  url.searchParams.set('channel', channel);
  url.searchParams.set('limit', String(limit));
  if (oldest) {
    url.searchParams.set('oldest', String(oldest));
  }

  const res = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json; charset=utf-8',
    },
  });

  if (!res.ok) {
    throw new Error(`Slack API HTTP error ${res.status}: ${res.statusText}`);
  }

  const data = await res.json();
  if (!data.ok) {
    throw formatSlackApiError(data.error, channel);
  }

  return data.messages || [];
}

export async function fetchConversationReplies(channel, ts, token) {
  let allMessages = [];
  let cursor = null;

  do {
    const url = new URL('https://slack.com/api/conversations.replies');
    url.searchParams.set('channel', channel);
    url.searchParams.set('ts', ts);
    url.searchParams.set('limit', '100');
    if (cursor) {
      url.searchParams.set('cursor', cursor);
    }

    const res = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json; charset=utf-8',
      },
    });

    if (!res.ok) {
      throw new Error(`Slack API HTTP error ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();
    if (!data.ok) {
      throw formatSlackApiError(data.error, channel, ts);
    }

    if (Array.isArray(data.messages)) {
      allMessages = allMessages.concat(data.messages);
    }

    cursor = data.response_metadata?.next_cursor || null;
  } while (cursor);

  return allMessages;
}

export function formatSlackApiError(errorCode, channel, ts = null) {
  const hints = {
    channel_not_found: `Channel "${channel}" not found or token has no access. Verify channel ID and permissions.`,
    not_in_channel: `Bot is not in channel "${channel}". Run "/invite @bot_name" in the Slack channel, or use a User Token (xoxp-...) instead.`,
    missing_scope: `Token is missing required OAuth scopes. Ensure it has: channels:history, groups:history, files:read, users:read.`,
    invalid_auth: `Slack authentication token is invalid or expired. Check token configuration in ~/.config/agent-harness/secrets.env.`,
    thread_not_found: `Thread with ts="${ts}" not found in channel "${channel}".`,
    ratelimited: `Slack API rate limit reached. Retry after a short delay.`,
  };

  const hint = hints[errorCode] || `Slack API returned error: "${errorCode}".`;
  return new Error(`[Slack API Error: ${errorCode}] ${hint}`);
}

export async function fetchUserInfo(userId, token, userCache) {
  if (!userId) return { name: 'Unknown', real_name: 'Unknown', display_name: 'Unknown' };
  if (userCache.has(userId)) return userCache.get(userId);

  try {
    const url = `https://slack.com/api/users.info?user=${encodeURIComponent(userId)}`;
    const res = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json; charset=utf-8',
      },
    });

    if (!res.ok) {
      const fallback = { name: userId, real_name: userId, display_name: userId };
      userCache.set(userId, fallback);
      return fallback;
    }

    const data = await res.json();
    if (data.ok && data.user) {
      const u = data.user;
      const profile = u.profile || {};
      const info = {
        id: userId,
        name: u.name || userId,
        real_name: profile.real_name || u.real_name || u.name || userId,
        display_name: profile.display_name || profile.real_name || u.name || userId,
      };
      userCache.set(userId, info);
      return info;
    }
  } catch (err) {
    // Network / info error, fallback to userId
  }

  const fallback = { name: userId, real_name: userId, display_name: userId };
  userCache.set(userId, fallback);
  return fallback;
}

// ==========================================
// 5. File & Image Downloader
// ==========================================
export async function downloadSlackFile(fileUrl, token, destinationPath) {
  let currentUrl = fileUrl;
  let redirectCount = 0;
  const maxRedirects = 6;

  while (redirectCount < maxRedirects) {
    const isSlackOrigin = currentUrl.includes('slack.com') || currentUrl.includes('slack-files.com');
    const headers = {};

    // S3 signed URLs reject requests that have both query params and Authorization header.
    // Only send Authorization header to Slack domains!
    if (isSlackOrigin) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(currentUrl, {
      method: 'GET',
      headers,
      redirect: 'manual',
    });

    if (res.status >= 300 && res.status < 400) {
      const location = res.headers.get('location');
      if (!location) {
        throw new Error(`HTTP ${res.status} redirect without Location header from ${currentUrl}`);
      }
      currentUrl = new URL(location, currentUrl).href;
      redirectCount++;
      continue;
    }

    if (!res.ok) {
      throw new Error(`Failed to download file (HTTP ${res.status}): ${res.statusText}`);
    }

    const arrayBuffer = await res.arrayBuffer();
    fs.writeFileSync(destinationPath, Buffer.from(arrayBuffer));
    return;
  }

  throw new Error(`Too many redirects downloading ${fileUrl}`);
}

function sanitizeFilename(name) {
  return (name || 'file')
    .replace(/[/\\?%*:|"<>]/g, '_')
    .replace(/\s+/g, '_')
    .slice(0, 100);
}

// ==========================================
// 6. Feedback Thread Detection & Scoring
// ==========================================
export function scoreFeedbackCandidate(msg, targetUserId = DEFAULT_TARGET_USER_ID) {
  const text = msg.text || '';
  let score = 0;

  const hasFeedback = /feedback/i.test(text);
  const hasThread = /#?thread/i.test(text);
  const hasTicket = /ticket/i.test(text) || /github\.com\/idx-vn/i.test(text) || /issues\/\d+/i.test(text) || /pull\/\d+/i.test(text);
  const hasUserMention = text.includes(`<@${targetUserId}>`) || msg.user === targetUserId;
  const replyCount = msg.reply_count || 0;
  const hasFiles = Boolean(msg.files && msg.files.length > 0);

  if (hasFeedback) score += 60;
  if (hasThread) score += 40;
  if (hasTicket) score += 50;
  if (hasUserMention) score += 35;
  if (hasFeedback && (hasThread || hasTicket)) score += 60;
  if (replyCount > 0) score += Math.min(replyCount * 5, 50);
  if (hasFiles) score += 10;

  const isCandidate = score > 0 || replyCount > 0;
  return { score, isCandidate, msg };
}

export function findFeedbackThreads(messages, { targetUserId = DEFAULT_TARGET_USER_ID, hours = null } = {}) {
  const cutoff = hours ? Date.now() / 1000 - parseFloat(hours) * 3600 : null;

  const candidates = [];
  for (const m of messages) {
    const tsNum = parseFloat(m.ts);
    if (cutoff && tsNum < cutoff) continue;

    const { score, isCandidate } = scoreFeedbackCandidate(m, targetUserId);
    if (isCandidate) {
      candidates.push({
        ts: m.thread_ts || m.ts,
        messageTs: m.ts,
        replyCount: m.reply_count || 0,
        user: m.user,
        text: m.text || '',
        score,
        msg: m,
      });
    }
  }

  // Deduplicate by thread root ts (keep highest score)
  const byTs = new Map();
  for (const c of candidates) {
    if (!byTs.has(c.ts) || byTs.get(c.ts).score < c.score) {
      byTs.set(c.ts, c);
    }
  }

  return Array.from(byTs.values()).sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    return parseFloat(b.ts) - parseFloat(a.ts);
  });
}

// ==========================================
// 7. Thread Formatter & Markdown Generator
// ==========================================
export function formatThreadMarkdown(meta, enrichedMessages) {
  const lines = [];
  lines.push(`# 🧵 Slack Thread: Channel \`${meta.channel}\` (ts: \`${meta.ts}\`)`);
  lines.push('');
  if (meta.originalUrl) {
    lines.push(`- **Original Link**: [Open in Slack](${meta.originalUrl})`);
  }
  lines.push(`- **Channel ID**: \`${meta.channel}\``);
  lines.push(`- **Thread TS**: \`${meta.ts}\``);
  lines.push(`- **Message Count**: ${enrichedMessages.length}`);
  lines.push(`- **Total Attachments/Images**: ${meta.totalFiles}`);
  lines.push(`- **Local Download Folder**: \`${meta.outDir}\``);

  if (meta.linkedGithubIssues && meta.linkedGithubIssues.length > 0) {
    lines.push(`- **Linked GitHub Tickets**: ${meta.linkedGithubIssues.map(u => `[${u}](${u})`).join(', ')}`);
  }
  if (meta.targetAssignee) {
    lines.push(`- **Target Assignee**: \`${meta.targetAssignee}\` (<@${meta.targetUserId || DEFAULT_TARGET_USER_ID}>)`);
  }

  lines.push('');
  lines.push('---');
  lines.push('');

  // Extract candidate target tasks if present
  const targetUserId = meta.targetUserId || DEFAULT_TARGET_USER_ID;
  const targetTasks = [];
  enrichedMessages.forEach((msg, idx) => {
    const text = msg.text || '';
    if (text.includes(`<@${targetUserId}>`) || /@Khánh Dương P\./i.test(text) || /khanhduong22/i.test(text)) {
      targetTasks.push({ msgIdx: idx + 1, text, files: msg.downloadedFiles || [] });
    }
  });

  if (targetTasks.length > 0) {
    lines.push(`## 🎯 Detected Direct Tasks for @Khánh Dương P. (${meta.targetAssignee || DEFAULT_TARGET_ASSIGNEE})`);
    lines.push('');
    targetTasks.forEach(t => {
      lines.push(`- **From Message #${t.msgIdx}**:`);
      const blockLines = t.text.split('\n').filter(l => l.trim().length > 0);
      blockLines.forEach(l => lines.push(`  > ${l}`));
      if (t.files.length > 0) {
        lines.push(`  - Attachments: ${t.files.map(f => `[\`${f.name}\`](file://${f.localPath})`).join(', ')}`);
      }
      lines.push('');
    });
    lines.push('---');
    lines.push('');
  }

  enrichedMessages.forEach((msg, idx) => {
    const author = msg.author?.display_name || msg.author?.real_name || msg.user || 'Unknown';
    const authorId = msg.user ? ` (${msg.user})` : '';
    const dateStr = msg.ts ? new Date(parseFloat(msg.ts) * 1000).toISOString() : '';
    const msgNum = idx === 0 ? '1 (Thread Parent)' : `${idx + 1}`;

    lines.push(`### Message #${msgNum}: **${author}**${authorId} — *${dateStr}*`);
    lines.push('');
    lines.push(msg.text ? msg.text : '*(No text message)*');
    lines.push('');

    if (msg.downloadedFiles && msg.downloadedFiles.length > 0) {
      lines.push(`📎 **Attached Files & Screenshots (${msg.downloadedFiles.length})**:`);
      msg.downloadedFiles.forEach(f => {
        const isImage = (f.mimetype || '').startsWith('image/') || /\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(f.name);
        const icon = isImage ? '🖼️ [Screenshot/Image]' : '📄 [File]';
        const sizeKb = f.size ? ` (${Math.round(f.size / 1024)} KB)` : '';
        lines.push(`- ${icon} **${f.name}**${sizeKb}`);
        lines.push(`  - Local Path: \`${f.localPath}\``);
        lines.push(`  - Markdown Link: [${f.name}](file://${f.localPath})`);
      });
      lines.push('');
    }

    lines.push('---');
    lines.push('');
  });

  lines.push('### 💡 Next Steps for Agent:');
  lines.push('1. **Inspect Screenshots**: Read attached screenshots using `read_file` on the local file paths above.');
  lines.push('2. **Check Parent Issue**: Query GitHub issue details (e.g. `gh issue view <issue> --json title,body,subIssues`).');
  lines.push('3. **Decompose & Create Sub-Issues**: Use `github-task-breakdown` to create native sub-issues for target assignee.');
  lines.push('4. **Reproduce & Fix**: Locate source components in `index-web`, `index-api`, or `index-admin-cms` and implement fixes at root cause.');
  lines.push('5. **Verify & Ship**: Run unit tests + `tsc --noEmit`, squash to 1 Conventional Commit, and create PR.');

  return lines.join('\n');
}

// ==========================================
// 8. Thread Processor
// ==========================================
export async function processThread({
  channel,
  ts,
  originalUrl = null,
  token,
  source,
  outDir = null,
  jsonOnly = false,
  skipImages = false,
  targetUserId = DEFAULT_TARGET_USER_ID,
  targetAssignee = DEFAULT_TARGET_ASSIGNEE,
}) {
  const sanitizedTsDir = ts.replace(/\./g, '_');
  const finalOutDir = outDir ? path.resolve(outDir) : path.join('/tmp', `slack-thread-${sanitizedTsDir}`);
  const attachmentsDir = path.join(finalOutDir, 'attachments');
  fs.mkdirSync(attachmentsDir, { recursive: true });

  if (!jsonOnly) {
    console.log(`\n🔍 Fetching Slack thread...`);
    console.log(`   Channel: ${channel}`);
    console.log(`   Thread TS: ${ts}`);
    if (originalUrl) console.log(`   URL: ${originalUrl}`);
    console.log(`   Token Source: ${source}`);
    console.log(`   Output Folder: ${finalOutDir}\n`);
  }

  // 1. Fetch all replies in thread
  const messages = await fetchConversationReplies(channel, ts, token);
  if (!messages || messages.length === 0) {
    throw new Error(`No messages found in thread for channel ${channel} and ts ${ts}`);
  }

  // 2. Resolve users and download files
  const userCache = new Map();
  let totalFiles = 0;
  const enrichedMessages = [];

  for (let mIdx = 0; mIdx < messages.length; mIdx++) {
    const msg = messages[mIdx];
    let authorInfo;
    if (msg.user) {
      authorInfo = await fetchUserInfo(msg.user, token, userCache);
    } else if (msg.username) {
      authorInfo = { name: msg.username, real_name: msg.username, display_name: msg.username };
    } else {
      authorInfo = { name: 'Bot/System', real_name: 'Bot/System', display_name: 'Bot/System' };
    }

    const downloadedFiles = [];
    if (!skipImages && Array.isArray(msg.files)) {
      for (let fIdx = 0; fIdx < msg.files.length; fIdx++) {
        const file = msg.files[fIdx];
        const downloadUrl = file.url_private_download || file.url_private;
        if (!downloadUrl) continue;

        const safeName = sanitizeFilename(file.name || `file_${fIdx}`);
        const filename = `${mIdx + 1}_${fIdx + 1}_${file.id}_${safeName}`;
        const destPath = path.join(attachmentsDir, filename);

        try {
          if (!jsonOnly) {
            process.stdout.write(`   ⬇️ Downloading: ${file.name || filename}... `);
          }
          await downloadSlackFile(downloadUrl, token, destPath);
          if (!jsonOnly) {
            process.stdout.write(`✓ (${Math.round(file.size / 1024 || 0)} KB)\n`);
          }

          downloadedFiles.push({
            id: file.id,
            name: file.name,
            mimetype: file.mimetype,
            size: file.size,
            localPath: destPath,
            originalDownloadUrl: downloadUrl,
          });
          totalFiles++;
        } catch (downloadErr) {
          if (!jsonOnly) {
            console.error(`FAILED (${downloadErr.message})`);
          }
          downloadedFiles.push({
            id: file.id,
            name: file.name,
            error: downloadErr.message,
          });
        }
      }
    }

    enrichedMessages.push({
      ...msg,
      author: authorInfo,
      downloadedFiles,
    });
  }

  // Extract linked github issues/tickets
  const allText = enrichedMessages.map(m => m.text || '').join('\n');
  const githubIssues = [...new Set(allText.match(/https:\/\/github\.com\/[^\s>|)]+/g) || [])];
  const targetMentions = enrichedMessages.filter(m => (m.text || '').includes(`<@${targetUserId}>`));

  const meta = {
    channel,
    ts,
    originalUrl: originalUrl || `https://itify-workspace.slack.com/archives/${channel}/p${ts.replace('.', '')}`,
    outDir: finalOutDir,
    attachmentsDir,
    totalFiles,
    messageCount: enrichedMessages.length,
    linkedGithubIssues: githubIssues,
    targetUserId,
    targetAssignee,
    hasTargetMentions: targetMentions.length > 0,
    fetchedAt: new Date().toISOString(),
  };

  const markdownContent = formatThreadMarkdown(meta, enrichedMessages);
  const jsonContent = JSON.stringify({ meta, messages: enrichedMessages }, null, 2);

  const mdFilePath = path.join(finalOutDir, 'summary.md');
  const jsonFilePath = path.join(finalOutDir, 'thread.json');

  fs.writeFileSync(mdFilePath, markdownContent, 'utf8');
  fs.writeFileSync(jsonFilePath, jsonContent, 'utf8');

  if (jsonOnly) {
    console.log(jsonContent);
  } else {
    console.log(`\n======================================================`);
    console.log(markdownContent);
    console.log(`======================================================\n`);
    console.log(`✅ Saved Markdown summary to: ${mdFilePath}`);
    console.log(`✅ Saved Raw JSON data to:     ${jsonFilePath}`);
    console.log(`📁 Local attachments folder:   ${attachmentsDir}\n`);
  }

  return { meta, messages: enrichedMessages, mdFilePath, jsonFilePath, attachmentsDir };
}

// ==========================================
// 9. Main CLI Orchestrator
// ==========================================
export async function main() {
  const args = process.argv.slice(2);

  // Self-test mode
  if (args.includes('--test')) {
    runSelfTest();
    return;
  }

  // Help
  if (args.includes('--help') || args.includes('-h')) {
    printHelp();
    return;
  }

  let inputUrl = null;
  let channelArg = null;
  let tsArg = null;
  let outDirArg = null;
  let explicitToken = null;
  let jsonOnly = false;
  let skipImages = false;
  let isLatest = false;
  let hoursArg = null;
  let limitArg = 25;
  let listOnly = false;
  let fetchAll = false;
  let targetUserArg = DEFAULT_TARGET_USER_ID;
  let assigneeArg = DEFAULT_TARGET_ASSIGNEE;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--channel') channelArg = args[++i];
    else if (arg === '--ts') tsArg = args[++i];
    else if (arg === '--out-dir') outDirArg = args[++i];
    else if (arg === '--token') explicitToken = args[++i];
    else if (arg === '--json') jsonOnly = true;
    else if (arg === '--skip-images') skipImages = true;
    else if (arg === '--latest') isLatest = true;
    else if (arg === '--hours') hoursArg = args[++i];
    else if (arg === '--limit') limitArg = parseInt(args[++i], 10) || 25;
    else if (arg === '--list') listOnly = true;
    else if (arg === '--all') fetchAll = true;
    else if (arg === '--user') targetUserArg = args[++i];
    else if (arg === '--assignee') assigneeArg = args[++i];
    else if (!arg.startsWith('-') && !inputUrl) inputUrl = arg;
  }

  const { token, source, secretsFile } = resolveSlackToken(explicitToken);

  if (!token) {
    console.error(`\x1b[31m❌ Error: No Slack token found.\x1b[0m\n`);
    console.error(`Please provide a Slack User or Bot token using one of these options:\n`);
    console.error(`1. Add to ${secretsFile || '~/.config/agent-harness/secrets.env'}:`);
    console.error(`   \x1b[32mSLACK_USER_TOKEN="xoxp-..."\x1b[0m   (Recommended - works across all channels you have access to)`);
    console.error(`   or`);
    console.error(`   \x1b[32mSLACK_BOT_TOKEN="xoxb-..."\x1b[0m    (Requires bot to be invited to channel via /invite @bot)\n`);
    console.error(`2. Required OAuth Scopes for your Slack App:`);
    console.error(`   - \x1b[36mchannels:history\x1b[0m (view public channel messages)`);
    console.error(`   - \x1b[36mgroups:history\x1b[0m   (view private channel messages)`);
    console.error(`   - \x1b[36mfiles:read\x1b[0m       (download screenshots and file attachments)`);
    console.error(`   - \x1b[36musers:read\x1b[0m       (resolve user display names)`);
    console.error(`   - \x1b[36mim:history, mpim:history\x1b[0m (optional: for direct messages)\n`);
    console.error(`3. Or pass via CLI:`);
    console.error(`   node fetch-slack-thread.mjs "<URL>" --token "xoxp-..."\n`);
    process.exit(1);
  }

  // Scan mode is triggered when no URL & no specific TS is provided, or when --latest/--hours/--list is passed
  const isScanMode = !inputUrl && !tsArg;

  if (isScanMode) {
    const channel = channelArg || DEFAULT_CHANNEL_ID;
    const fetchLimit = hoursArg ? Math.max(limitArg, 50) : limitArg;
    const oldest = hoursArg ? Date.now() / 1000 - parseFloat(hoursArg) * 3600 : null;

    if (!jsonOnly) {
      console.log(`📡 Scanning Slack channel: ${channel} (limit: ${fetchLimit}${hoursArg ? `, hours: ${hoursArg}` : ''})...`);
    }

    const historyMessages = await fetchConversationHistory(channel, token, fetchLimit, oldest);
    const candidates = findFeedbackThreads(historyMessages, { targetUserId: targetUserArg, hours: hoursArg });

    if (candidates.length === 0) {
      throw new Error(`No active feedback threads found in channel "${channel}"${hoursArg ? ` within the last ${hoursArg} hours` : ''}.`);
    }

    if (listOnly) {
      console.log(`\n📋 Found ${candidates.length} active candidate thread(s) in ${channel}:\n`);
      candidates.forEach((c, idx) => {
        const preview = c.text.replace(/\n/g, ' ').slice(0, 90);
        const slackUrl = `https://itify-workspace.slack.com/archives/${channel}/p${c.ts.replace('.', '')}`;
        console.log(`[${idx + 1}] TS: ${c.ts} | Score: ${c.score} | Replies: ${c.replyCount} | Author: ${c.user}`);
        console.log(`    Text: "${preview}..."`);
        console.log(`    URL:  ${slackUrl}\n`);
      });
      return;
    }

    if (fetchAll) {
      if (!jsonOnly) {
        console.log(`🎯 Processing ALL ${candidates.length} candidate thread(s)...`);
      }
      for (const cand of candidates) {
        const originalUrl = `https://itify-workspace.slack.com/archives/${channel}/p${cand.ts.replace('.', '')}`;
        await processThread({
          channel,
          ts: cand.ts,
          originalUrl,
          token,
          source,
          outDir: outDirArg ? path.join(outDirArg, cand.ts.replace('.', '_')) : null,
          jsonOnly,
          skipImages,
          targetUserId: targetUserArg,
          targetAssignee: assigneeArg,
        });
      }
      return;
    }

    // Default or --latest: pick top candidate
    const top = candidates[0];
    const topUrl = `https://itify-workspace.slack.com/archives/${channel}/p${top.ts.replace('.', '')}`;
    if (!jsonOnly) {
      console.log(`🎯 Auto-selected latest feedback thread:`);
      console.log(`   Thread TS: ${top.ts} (Score: ${top.score}, Replies: ${top.replyCount})`);
      console.log(`   URL: ${topUrl}`);
      console.log(`   Preview: "${top.text.replace(/\n/g, ' ').slice(0, 100)}..."\n`);
    }

    await processThread({
      channel,
      ts: top.ts,
      originalUrl: topUrl,
      token,
      source,
      outDir: outDirArg,
      jsonOnly,
      skipImages,
      targetUserId: targetUserArg,
      targetAssignee: assigneeArg,
    });
    return;
  }

  // Single explicit thread mode
  const { channel, ts, originalUrl } = parseSlackUrlOrArgs(inputUrl, channelArg, tsArg);

  await processThread({
    channel,
    ts,
    originalUrl,
    token,
    source,
    outDir: outDirArg,
    jsonOnly,
    skipImages,
    targetUserId: targetUserArg,
    targetAssignee: assigneeArg,
  });
}

// ==========================================
// 10. Self Test & Diagnostics
// ==========================================
function runSelfTest() {
  console.log('🧪 Running fetch-slack-thread.mjs self-tests...');

  // Test 1: URL parser with standard URL
  const testUrl1 = 'https://itify-workspace.slack.com/archives/C09E30T7V7T/p1793345354377479';
  const res1 = parseSlackUrlOrArgs(testUrl1);
  if (res1.channel !== 'C09E30T7V7T' || res1.ts !== '1793345354.377479') {
    throw new Error(`Self-test 1 failed: ${JSON.stringify(res1)}`);
  }
  console.log('  ✓ Test 1 passed: Standard Slack URL parsed correctly (Channel: C09E30T7V7T, TS: 1793345354.377479)');

  // Test 2: URL with thread_ts query param
  const testUrl2 = 'https://itify-workspace.slack.com/archives/C09E30T7V7T/p1793345399999999?thread_ts=1793345354.377479&cid=C09E30T7V7T';
  const res2 = parseSlackUrlOrArgs(testUrl2);
  if (res2.channel !== 'C09E30T7V7T' || res2.ts !== '1793345354.377479') {
    throw new Error(`Self-test 2 failed: ${JSON.stringify(res2)}`);
  }
  console.log('  ✓ Test 2 passed: Thread reply URL with thread_ts query param parsed correctly');

  // Test 3: Direct args
  const res3 = parseSlackUrlOrArgs(null, 'C012345', '123456.789000');
  if (res3.channel !== 'C012345' || res3.ts !== '123456.789000') {
    throw new Error(`Self-test 3 failed: ${JSON.stringify(res3)}`);
  }
  console.log('  ✓ Test 3 passed: Explicit channel and timestamp args parsed correctly');

  // Test 4: Secrets loader
  const { secretsFile, envVars } = loadSecrets();
  console.log(`  ✓ Test 4 passed: Secrets loader checked "${secretsFile}". Found keys: ${Object.keys(envVars).join(', ') || 'none'}`);

  // Test 5: Markdown formatting
  const mockMeta = {
    channel: 'C09E30T7V7T',
    ts: '1793345354.377479',
    originalUrl: testUrl1,
    outDir: '/tmp/slack-test',
    totalFiles: 1,
    targetUserId: DEFAULT_TARGET_USER_ID,
    targetAssignee: DEFAULT_TARGET_ASSIGNEE,
  };
  const mockMessages = [
    {
      user: 'U01234',
      text: 'Bug report with screenshot',
      ts: '1793345354.377479',
      author: { display_name: 'Tester', real_name: 'Tester Real' },
      downloadedFiles: [
        {
          name: 'bug.png',
          mimetype: 'image/png',
          size: 10240,
          localPath: '/tmp/slack-test/attachments/1_1_F123_bug.png',
        },
      ],
    },
  ];
  const md = formatThreadMarkdown(mockMeta, mockMessages);
  if (!md.includes('Bug report with screenshot') || !md.includes('bug.png')) {
    throw new Error('Self-test 5 failed: Markdown format check');
  }
  console.log('  ✓ Test 5 passed: Markdown summary generated accurately');

  // Test 6: Feedback scoring logic
  const feedbackMsg = {
    ts: '1793345354.377479',
    text: '*#Thread feedback STG -30/10*\n*Ticket:* https://github.com/idx-vn/index-web/issues/3844',
    reply_count: 15,
  };
  const regularMsg = {
    ts: '1793340000.000000',
    text: 'Good morning everyone',
    reply_count: 0,
  };
  const scoredFeedback = scoreFeedbackCandidate(feedbackMsg, DEFAULT_TARGET_USER_ID);
  const scoredRegular = scoreFeedbackCandidate(regularMsg, DEFAULT_TARGET_USER_ID);
  if (scoredFeedback.score <= scoredRegular.score || scoredFeedback.score < 100) {
    throw new Error(`Self-test 6 failed: Feedback score (${scoredFeedback.score}) should exceed regular (${scoredRegular.score})`);
  }
  console.log(`  ✓ Test 6 passed: Feedback scoring evaluates correctly (feedback=${scoredFeedback.score}, regular=${scoredRegular.score})`);

  // Test 7: findFeedbackThreads ranking
  const history = [regularMsg, feedbackMsg];
  const ranked = findFeedbackThreads(history, { targetUserId: DEFAULT_TARGET_USER_ID });
  if (ranked.length === 0 || ranked[0].ts !== feedbackMsg.ts) {
    throw new Error(`Self-test 7 failed: Ranked thread should be feedbackMsg (${feedbackMsg.ts})`);
  }
  console.log(`  ✓ Test 7 passed: Feedback threads sorted and ranked properly`);

  console.log('\n🎉 All self-tests passed successfully!\n');
}

function printHelp() {
  console.log(`
Slack Thread & Feedback Auto-Scanner
====================================
Scans Slack channels (default: #index-dev C09E30T7V7T) or fetches specific threads,
downloads all attached screenshots and videos, and produces structured Markdown
and JSON summaries for autonomous bug fixing and GitHub task creation.

Usage:
  # Auto-scan latest feedback thread in #index-dev:
  node fetch-slack-thread.mjs --latest
  node fetch-slack-thread.mjs

  # Fetch specific Slack thread:
  node fetch-slack-thread.mjs "<SLACK_THREAD_URL>" [options]

  # Fetch specific channel & timestamp:
  node fetch-slack-thread.mjs --channel C09E30T7V7T --ts 1793345354.377479

  # List active feedback threads from last 24 hours without downloading:
  node fetch-slack-thread.mjs --hours 24 --list

  # Fetch ALL active feedback threads from last 24 hours:
  node fetch-slack-thread.mjs --hours 24 --all

Options:
  --latest          Scan channel and select the latest feedback thread (default when no URL provided)
  --channel <id>    Slack Channel ID (default: C09E30T7V7T for #index-dev)
  --ts <timestamp>  Slack Message timestamp (e.g. 1793345354.377479)
  --hours <hours>   Scan messages within the last N hours (e.g. --hours 24)
  --limit <count>   Max channel history messages to scan (default: 25)
  --list            List detected candidate threads without downloading full replies
  --all             Fetch replies and attachments for ALL detected candidate threads
  --user <id>       Target Slack User ID to track/score (default: U09NR1YEC3Y / @Khánh Dương P.)
  --assignee <gh>   Target GitHub assignee username (default: khanhduong22)
  --token <token>   Pass Slack token directly (xoxp-... or xoxb-...)
  --out-dir <dir>   Custom output directory (default: /tmp/slack-thread-<ts>/)
  --json            Print JSON payload to stdout
  --skip-images     Fetch text messages only, skip downloading files
  --test            Run internal self-tests
  --help, -h        Show this help message

Authentication:
  Configure your token in ~/.config/agent-harness/secrets.env:
    SLACK_USER_TOKEN="xoxp-..."    (Recommended: user token with access to #index-dev)
    or
    SLACK_BOT_TOKEN="xoxb-..."     (Requires bot invitation to channel)

Required Slack OAuth Scopes:
  - channels:history  (public channels)
  - groups:history    (private channels)
  - files:read        (file attachments & screenshots)
  - users:read        (user display names)
`);
}

// Run when executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(err => {
    console.error(`\x1b[31mError:\x1b[0m ${err.message}`);
    process.exit(1);
  });
}
