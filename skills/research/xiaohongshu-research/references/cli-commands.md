# CLI 子命令 + 数据结构参考

来源：`uv run python scripts/cli.py --help` 与实测返回。exit code：0=成功，1=未登录，2=错误。

## 认证
| 子命令 | 说明 |
|---|---|
| `check-login` | 检查登录状态，返回 `{"logged_in": true/false}` |
| `login` | 扫码登录（阻塞等待） |
| `get-qrcode` | 获取登录二维码（非阻塞），配合 `wait-login` |
| `phone-login` / `send-code --phone X` / `verify-code --code Y` | 手机验证码登录 |
| `delete-cookies` | 退出/切换账号 |

## 浏览（只读，做报告主要用这些）
| 子命令 | 说明 |
|---|---|
| `list-feeds` | 首页推荐 Feed |
| `search-feeds --keyword K [筛选]` | 关键词搜索 |
| `get-feed-detail --feed-id ID --xsec-token T [--load-all-comments] [--click-more-replies]` | 笔记详情+评论 |
| `user-profile --user-id U --xsec-token T` | 用户主页 |

`search-feeds` 筛选参数：
- `--sort-by` 综合(默认)/最新/最多点赞/最多评论/最多收藏
- `--note-type` 不限/视频/图文
- `--publish-time` 不限/一天内/一周内/半年内
- `--search-scope` 不限/已看过/未看过/已关注
- `--location` 不限/同城/附近

## 互动 / 发布（需用户确认，报告流程一般不碰）
`post-comment` `reply-comment` `like-feed` `favorite-feed` `publish` `publish-video`
`fill-publish` `click-publish` `save-draft` `long-article` `select-template` `next-step`

## 风控诊断
| 子命令 | 说明 |
|---|---|
| `check-risk` | 浏览器指纹 + API 探测 + 是否弹验证码，返回 risk_level/issue/fingerprints |
| `risk-report` | 基于 NetLog 生成结构化风控报告 |
| `get-netlog` | NetLog 原始 entries（需先在扩展 popup 连点标题 5 次激活彩蛋） |
| `diagnose-404` | 拦截器捕获的 404 根因诊断 |

## 数据结构

### search-feeds 返回
```json
{
  "feeds": [{
    "id": "6a9ff42d00000000280346ee",
    "xsecToken": "AB...=",
    "modelType": "note",          // note | live_v2 | hot_query（后两种可跳过）
    "displayTitle": "...",
    "type": "normal",             // normal(图文) | video
    "user": {"userId": "...", "nickname": "..."},
    "interactInfo": {"likedCount":"6899","collectedCount":"8669","commentCount":"138","sharedCount":""},
    "cover": "http://..."
  }],
  "count": 44
}
```

### get-feed-detail 返回
```json
{
  "note": {
    "noteId": "...", "title": "...", "desc": "...", "body": "...",
    "tags": ["#..."], "type": "normal|video",
    "time": 1788922828000,        // 毫秒时间戳
    "ipLocation": "北京",
    "user": {"userId":"...","nickname":"..."},
    "interactInfo": {"likedCount":"...","collectedCount":"...","commentCount":"..."},
    "imageList": [{"urlDefault":"..."}]
  },
  "comments": [{
    "id":"...","content":"...","likeCount":"17","createTime":1789066770000,
    "ipLocation":"德国","user":{"nickname":"..."},
    "subCommentCount":"11",
    "subComments":[{"id":"...","content":"...","likeCount":"0","user":{"nickname":"..."}}]
  }]
}
```

## 内容类型分层（观察：小红书泛关键词的三层语义）
1. **内容方法论层**（高互动、有真讨论）：权威 IP 观点、反鸡汤深度图文、第一性原理
2. **本地社群层**（低互动长尾）：某城市 OPC/线下活动/注册补贴/找搭子
3. **引流营销层**（中互动、评论区全是「pm」）：月入 XX、AI 副业、私信领流程

做评估报告时按此分层，聚焦第 1 层 + 高互动的第 3 层样本。
