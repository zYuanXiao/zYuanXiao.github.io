# Zhiyuan Xiao - Personal Homepage

这是一个无需构建工具的单页学术主页。页面主体在 `index.html`，字体通过 Google Fonts 加载；字体不可用时会自动使用系统字体。

## 本地预览

在当前目录运行：

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

然后访问 `http://127.0.0.1:8765/`。

## 素材目录

- `assets/companies/standard-robotics.png`：Standard Robotics 品牌标记。
- `assets/companies/deepano.png`：Deepano Technology 英文字标。
- `assets/companies/definesys.png`：Definesys 的图形标记与“得帆”主品牌，不包含宣传口号。
- `assets/profile/zhiyuan-xiao.jpg`：主页头像，由用户提供的原图生成。
- `assets/publications/aurora-before-after.jpg`：Aurora 官方案例的 Source / Aurora 对比图。

页面使用本地图片，部署后不依赖素材来源网站持续在线。`tools/build_assets.swift` 记录了公司 logo、头像和 Publication 图片的处理方式。

## 素材来源

- Standard Robotics：https://standard-robots.com/
- Deepano Technology：https://www.deepano.com/
- Definesys：https://www.definesys.com/
- Aurora Project Page：https://www.yongshengyu.com/Aurora-Page/

## 个人资料

- Email、GitHub、LinkedIn、Paper 和 Project 链接直接维护在 `index.html`。
- 联系邮箱：`xzzzzy666@gmail.com`。
- CV 文件已包含在项目根目录：`Zhiyuan_Xiao_CV.pdf`。
- 头像使用 `assets/profile/zhiyuan-xiao.jpg`；需要更换时，使用同名方形图片并保持 `512 x 512` 像素。

## GitHub Pages 部署

将 `index.html`、`README.md`、`assets/` 目录以及 `Zhiyuan_Xiao_CV.pdf` 上传到 GitHub Pages 仓库。静态资源均使用相对路径，无需额外构建步骤。
