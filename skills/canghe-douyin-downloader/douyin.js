#!/usr/bin/env node

/**
 * 抖音无水印视频下载和文案提取工具 (Node.js 版本)
 * 
 * 功能:
 * 1. 从抖音分享链接获取无水印视频下载链接
 * 2. 下载视频并提取音频
 * 3. 使用硅基流动 API 从音频中提取文本
 * 4. 自动保存文案到文件
 * 
 * 环境变量:
 * - DOUYIN_API_KEY: 硅基流动 API 密钥 (用于文案提取功能)
 * 
 * 使用示例:
 *   node douyin.js info "抖音分享链接"
 *   node douyin.js download "抖音分享链接" -o ./videos
 *   node douyin.js extract "抖音分享链接" -o ./output
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');
const https = require('https');
const http = require('http');
const { URL } = require('url');

// 配置
const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/121.0.2277.107 Version/17.0 Mobile/15E148 Safari/604.1'
};

const DEFAULT_API_BASE_URL = 'https://api.siliconflow.cn/v1/audio/transcriptions';
const DEFAULT_MODEL = 'FunAudioLLM/SenseVoiceSmall';

// 工具函数：Promise 版本的 http 请求
function httpRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const client = parsedUrl.protocol === 'https:' ? https : http;
    
    const opts = {
      method: options.method || 'GET',
      headers: { ...HEADERS, ...options.headers }
    };
    
    const req = client.request(url, opts, (res) => {
      if (options.stream) {
        resolve(res);
        return;
      }
      
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve(json);
        } catch {
          resolve(data);
        }
      });
    });
    
    req.on('error', reject);
    req.setTimeout(30000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
    
    if (options.body) {
      req.write(options.body);
    }
    req.end();
  });
}

// 工具函数：下载文件
async function downloadFile(url, filepath, showProgress = true) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const client = parsedUrl.protocol === 'https:' ? https : http;
    
    const req = client.get(url, { headers: HEADERS }, (res) => {
      // 处理重定向
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        downloadFile(res.headers.location, filepath, showProgress)
          .then(resolve)
          .catch(reject);
        return;
      }
      
      if (res.statusCode !== 200) {
        reject(new Error(`HTTP ${res.statusCode}`));
        return;
      }
      
      const totalSize = parseInt(res.headers['content-length'] || '0', 10);
      let downloaded = 0;
      
      const writer = fs.createWriteStream(filepath);
      
      res.on('data', (chunk) => {
        downloaded += chunk.length;
        if (showProgress && totalSize > 0) {
          const progress = (downloaded / totalSize * 100).toFixed(1);
          process.stdout.write(`\r下载进度: ${progress}%`);
        }
      });
      
      res.pipe(writer);
      
      writer.on('finish', () => {
        if (showProgress) console.log(`\n文件已保存: ${filepath}`);
        resolve(filepath);
      });
      
      writer.on('error', reject);
    });
    
    req.on('error', reject);
    req.setTimeout(60000, () => {
      req.destroy();
      reject(new Error('Download timeout'));
    });
  });
}

// 工具函数：运行 ffmpeg
function runFfmpeg(args) {
  return new Promise((resolve, reject) => {
    const ffmpegPath = 'ffmpeg';
    const proc = spawn(ffmpegPath, args);
    
    let stderr = '';
    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    proc.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`ffmpeg exited with code ${code}: ${stderr}`));
      }
    });
    
    proc.on('error', reject);
  });
}

// 工具函数：获取媒体信息
function getMediaInfo(filepath) {
  return new Promise((resolve) => {
    const proc = spawn('ffprobe', [
      '-v', 'quiet',
      '-print_format', 'json',
      '-show_format',
      filepath
    ]);
    
    let stdout = '';
    proc.stdout.on('data', (data) => { stdout += data.toString(); });
    proc.on('close', (code) => {
      if (code === 0) {
        try {
          const info = JSON.parse(stdout);
          resolve({
            duration: parseFloat(info.format?.duration || '0'),
            size: parseInt(info.format?.size || '0', 10)
          });
        } catch {
          resolve({ duration: 0, size: fs.statSync(filepath).size });
        }
      } else {
        resolve({ duration: 0, size: fs.statSync(filepath).size });
      }
    });
  });
}

// 跟踪重定向获取真实 URL
function followRedirect(url) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const client = parsedUrl.protocol === 'https:' ? https : http;

    const req = client.request(url, { method: 'GET', headers: HEADERS }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        const location = res.headers.location;
        const redirectUrl = location.startsWith('http') ? location : `${parsedUrl.protocol}//${parsedUrl.host}${location}`;
        resolve(redirectUrl);
      } else {
        resolve(url);
      }
      res.resume();
    });
    req.on('error', reject);
    req.setTimeout(15000, () => { req.destroy(); reject(new Error('Redirect timeout')); });
    req.end();
  });
}

// 解析抖音分享链接
async function parseShareUrl(shareText) {
  // 提取 URL
  const urlMatch = shareText.match(/https?:\/\/[^\s]+/);
  if (!urlMatch) {
    throw new Error('未找到有效的分享链接');
  }

  let shareUrl = urlMatch[0];

  // 如果是短链，先跟踪重定向获取真实 URL
  if (shareUrl.includes('v.douyin.com')) {
    shareUrl = await followRedirect(shareUrl);
  }

  // 从真实 URL 中提取数字视频 ID
  const videoIdMatch = shareUrl.match(/\/video\/(\d+)/);
  const awemeId = videoIdMatch ? videoIdMatch[1] : shareUrl.split('/').pop().split('?')[0];

  // 获取视频详情
  const apiUrl = `https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id=${awemeId}`;

  try {
    const apiResponse = await httpRequest(apiUrl, { headers: HEADERS });
    
    let videoData = apiResponse.aweme_detail || apiResponse;
    
    // 尝试从页面获取
    if (!videoData || !videoData.video) {
      const pageUrl = shareUrl.includes('douyin.com') ? shareUrl : `https://www.douyin.com${shareUrl}`;
      const pageContent = await httpRequest(pageUrl, { headers: HEADERS });
      
      if (typeof pageContent === 'string') {
        const match = pageContent.match(/window\._ROUTER_DATA\s*=\s*(.*?)<\/script>/);
        if (match) {
          const jsonData = JSON.parse(match[1]);
          const loaderData = jsonData.loaderData || jsonData;
          videoData = loaderData['video_(id)/page']?.videoInfoRes?.item_list?.[0] ||
                     loaderData['note_(id)/page']?.videoInfoRes?.item_list?.[0];
        }
      }
    }
    
    if (!videoData) {
      // 尝试从 redirect URL 获取
      throw new Error('无法解析视频信息');
    }
    
    const videoUrl = videoData.video?.play_addr?.url_list?.[0]?.replace('playwm', 'play') ||
                     videoData.video?.download_addr?.url_list?.[0];
    const desc = videoData.desc || `douyin_${videoData.video?.id || 'unknown'}`;
    const videoId = videoData.video?.id || videoData.aweme_id;
    
    return {
      url: videoUrl,
      title: desc.replace(/[\\/:*?"<>|]/g, '_'),
      video_id: videoId
    };
  } catch (error) {
    throw new Error(`解析视频信息失败: ${error.message}`);
  }
}

// 下载视频
async function downloadVideo(videoInfo, outputDir, showProgress = true) {
  const outputPath = path.join(outputDir, `${videoInfo.video_id}.mp4`);
  
  if (showProgress) {
    console.log(`正在下载视频: ${videoInfo.title}`);
  }
  
  await downloadFile(videoInfo.url, outputPath, showProgress);
  
  return outputPath;
}

// 提取音频
async function extractAudio(videoPath, showProgress = true) {
  const audioPath = videoPath.replace(/\.mp4$/, '.mp3');
  
  if (showProgress) {
    console.log('正在提取音频...');
  }
  
  await runFfmpeg([
    '-i', videoPath,
    '-vn',
    '-acodec', 'libmp3lame',
    '-q:a', '0',
    '-y',
    audioPath
  ]);
  
  if (showProgress) {
    console.log(`音频已保存: ${audioPath}`);
  }
  
  return audioPath;
}

// 语音转文字
async function transcribeAudio(audioPath, apiKey, showProgress = true) {
  if (showProgress) {
    console.log('正在识别语音...');
  }
  
  // 读取音频文件
  const audioBuffer = fs.readFileSync(audioPath);
  
  // 创建 FormData
  const boundary = '----FormBoundary' + Math.random().toString(36).substring(2);
  const body = Buffer.concat([
    Buffer.from(`--${boundary}\r\n`),
    Buffer.from(`Content-Disposition: form-data; name="file"; filename="${path.basename(audioPath)}"\r\n`),
    Buffer.from('Content-Type: audio/mpeg\r\n\r\n'),
    audioBuffer,
    Buffer.from(`\r\n--${boundary}\r\n`),
    Buffer.from(`Content-Disposition: form-data; name="model"\r\n\r\n${DEFAULT_MODEL}\r\n`),
    Buffer.from(`--${boundary}--\r\n`)
  ]);
  
  const response = await httpRequest(DEFAULT_API_BASE_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': `multipart/form-data; boundary=${boundary}`,
      'Content-Length': body.length
    },
    body: body
  });
  
  if (response.text) {
    return response.text;
  }
  
  return JSON.stringify(response);
}

// 提取文案主函数
async function extractText(shareLink, apiKey, outputDir, saveVideo = false, showProgress = true) {
  if (!apiKey) {
    apiKey = process.env.DOUYIN_API_KEY || process.env.API_KEY;
  }
  
  if (!apiKey) {
    throw new Error('未设置 API 密钥，请设置 DOUYIN_API_KEY 或 API_KEY 环境变量');
  }
  
  if (showProgress) {
    console.log('正在解析抖音分享链接...');
  }
  
  const videoInfo = await parseShareUrl(shareLink);
  
  if (showProgress) {
    console.log('正在下载视频...');
  }
  
  const videoPath = await downloadVideo(videoInfo, outputDir, showProgress);
  
  if (showProgress) {
    console.log('正在提取音频...');
  }
  
  const audioPath = await extractAudio(videoPath, showProgress);
  
  if (showProgress) {
    console.log('正在从音频中提取文本...');
  }
  
  const textContent = await transcribeAudio(audioPath, apiKey, showProgress);
  
  // 保存文案
  const outputPath = path.join(outputDir, videoInfo.video_id, 'transcript.md');
  const outputFolder = path.dirname(outputPath);
  
  fs.mkdirSync(outputFolder, { recursive: true });
  
  const markdown = `# ${videoInfo.title}

| 属性 | 值 |
|------|-----|
| 视频ID | \`${videoInfo.video_id}\` |
| 提取时间 | ${new Date().toLocaleString('zh-CN')} |
| 下载链接 | [点击下载](${videoInfo.url}) |

---

## 文案内容

${textContent}
`;
  
  fs.writeFileSync(outputPath, markdown, 'utf-8');
  
  if (showProgress) {
    console.log(`文案已保存到: ${outputPath}`);
  }
  
  // 清理临时文件
  if (!saveVideo) {
    try { fs.unlinkSync(videoPath); } catch {}
  }
  try { fs.unlinkSync(audioPath); } catch {}
  
  return {
    video_info: videoInfo,
    text: textContent,
    output_path: outputPath
  };
}

// 主入口
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  const shareLink = args[1];
  
  if (!command || !shareLink) {
    console.log(`
抖音无水印视频下载和文案提取工具

用法:
  node douyin.js info <分享链接>      - 获取视频信息
  node douyin.js download <链接> -o <目录>  - 下载视频
  node douyin.js extract <链接> -o <目录>   - 提取文案
  
环境变量:
  DOUYIN_API_KEY 或 API_KEY  - 硅基流动 API 密钥
`);
    process.exit(1);
  }
  
  // 解析参数
  let outputDir = './output';
  let saveVideo = false;
  
  for (let i = 2; i < args.length; i++) {
    if (args[i] === '-o' && args[i + 1]) {
      outputDir = args[i + 1];
      i++;
    } else if (args[i] === '-v' || args[i] === '--save-video') {
      saveVideo = true;
    }
  }
  
  try {
    if (command === 'info') {
      const info = await parseShareUrl(shareLink);
      console.log('\n' + '='.repeat(50));
      console.log('视频信息:');
      console.log('='.repeat(50));
      console.log(`视频ID: ${info.video_id}`);
      console.log(`标题: ${info.title}`);
      console.log(`下载链接: ${info.url}`);
      console.log('='.repeat(50));
      
    } else if (command === 'download') {
      const videoInfo = await parseShareUrl(shareLink);
      const videoPath = await downloadVideo(videoInfo, outputDir);
      console.log(`\n视频已保存到: ${videoPath}`);
      
    } else if (command === 'extract') {
      const result = await extractText(shareLink, null, outputDir, saveVideo);
      console.log('\n' + '='.repeat(50));
      console.log('提取完成!');
      console.log('='.repeat(50));
      console.log(`视频ID: ${result.video_info.video_id}`);
      console.log(`标题: ${result.video_info.title}`);
      console.log(`保存位置: ${result.output_path}`);
      console.log('='.repeat(50));
      console.log('\n文案内容:\n');
      console.log(result.text.slice(0, 500) + '...' || result.text);
      console.log('\n' + '='.repeat(50));
    }
    
  } catch (error) {
    console.error(`错误: ${error.message}`);
    process.exit(1);
  }
}

main();

