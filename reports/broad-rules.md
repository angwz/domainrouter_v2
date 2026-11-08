# 宽泛规则清单

列出两类规则，判定依据见项目文档 docs/rules/broad-rules.md：

- **已过滤**：上游规则中范围接近全部流量或使用通用词关键词的条目，未写入规则文件；
- **已发布**：仍在规则文件中、但范围较大的规则，按类别和文件列出，供你检查。

手写在 my.wei 中的规则不会被过滤，单独标为「手写」。

## 已过滤（0）

没有。

## 已发布：DOMAIN-KEYWORD（177）

`clash-classic/AI-classic.yaml` → 🗨️ ChatGPT

- 子串匹配：`alkalimakersuite-pa.clients6.google.com` `colab` `developerprofiles` `generativelanguage` `openai` `twitter`

`clash-classic/America-classic.yaml` → ⛳ 美国专线

- 子串匹配：`adobe`

`clash-classic/Apple-classic.yaml` → 🍎 Apple

- 子串匹配：`apple-support.akadns.net` `apple.com.akadns.net` `apple.com.edgekey.net` `buy.itunes.apple.com` `icloud.com.akadns.net` `smp-device` `testflight`

`clash-classic/China-classic.yaml` → DIRECT

- 子串匹配：`.tmall.com` `alicdn` `alipay` `aliyun` `amp-api.podcasts.apple.com` `anti-ad.net` `api-adservices.apple.com` `api.smoot.apple.cn` `api.smoot.apple.com` `aw-s.tripcdn.com` `ax1x.com` `baidu` `beplay` `bfzycdn.com` `bilibili` `buy.itunes.apple.com` `cnki.net` `ctc.qzs.qzone.qq.com` `deepdyve` `els-cdn` `elsevier` `ess.apple.com` `gsa.apple.com` `hnagroup` `humb.apple.com` `icloud.com` `ls.apple.com` `microsoft` `o.lencr.org` `officecdn` `pkulaw` `push.apple.com` `readcube` `sciencedirect` `ssl.apple.com` `stripe` `taobao` `trip.com` `ttcdn-tos.kkimg.cc` `vip.ffzy-online` `vip.ffzy-play` `vip.kuaikan-cdn` `vip.lz-cdn` `wanfangdata` `wb_ad` `weather-adge.apple.com` `weather-edge.apple.com` `weibo` `westlawchina`
- 短关键词（4 个字符）：`qiyi`

`clash-classic/ChinaMedia-classic.yaml` → DIRECT

- 子串匹配：`bilibili` `epicgames` `steambroadcast` `steamstore` `steamuserimages`
- 短关键词（4 个字符）：`qiyi`

`clash-classic/Direct-classic.yaml` → DIRECT

- 子串匹配：`aria2` `thunder` `xlliveud` `xunlei` `yunpan`

`clash-classic/Google-classic.yaml` → 📩 Google

- 子串匹配：`appspot` `blogspot` `gmail` `google` `recaptcha`

`clash-classic/HK-classic.yaml` → 🛫 香港专线

- 手写 · 子串匹配：`annas-archive`
- 子串匹配：`github` `paypal` `steambroadcast` `steamstore` `steamuserimages`

`clash-classic/Japan-classic.yaml` → 🌺 日本专线

- 子串匹配：`avoddashs` `spotify`

`clash-classic/Media-classic.yaml` → 🛖 国际流媒体

- 子串匹配：`abematv.akamaized.net` `anthropic` `apiproxy-device-prod-nlb-` `avoddashs` `bbcfmt` `claude` `discovery.uplynk.com` `dualstack.apiproxy-` `dualstack.ichnaea-web-` `hamivideo.cdn.hinet.net` `hbogoasia` `japonx` `japronx` `jooxweb-api` `netflixdnstest` `nivod` `nowtv100` `olevod` `rthklive` `spotify` `tiktokcdn` `ttvnw` `tvbanywhere` `uk-live` `voddazn` `youtube`

`clash-classic/Microsoft-classic.yaml` → 🪟 Microsoft

- 短关键词（4 个字符）：`1drv`
- 子串匹配：`hotmail` `microsoft` `onedrive` `skydrive`

`clash-classic/NS-classic.yaml` → 🏖️ Community

- 手写 · 子串匹配：`nodeseek`

`clash-classic/Netflix-classic.yaml` → 🎬 Netflix

- 子串匹配：`apiproxy-device-prod-nlb-` `dualstack.apiproxy-` `dualstack.ichnaea-web-` `netflixdnstest`

`clash-classic/OneDrive-classic.yaml` → ⛅ OneDrive

- 短关键词（4 个字符）：`1drv`
- 子串匹配：`announce` `chdbits` `m-team` `onedrive` `skydrive` `torrent`

`clash-classic/Proxy-classic.yaml` → 🌠 节点选择

- 短关键词（4 个字符）：`1drv` `avtb` `porn`
- 子串匹配：`1e100` `abema` `amazon` `appledaily` `avoddashs` `bbcfmt` `beetalk` `blogspot` `dlercloud` `dropbox` `facebook` `fbcdn` `gmail` `google` `instagram` `musical.ly` `onedrive` `paypal` `pinterest` `sci-hub` `skydrive` `spotify` `telegram` `tiktok` `ttvnw` `twimg` `twitter` `uk-live` `voddazn` `whatsapp` `wikileaks` `youtube`
- 短关键词（3 个字符）：`jav`

`clash-classic/Singapore-classic.yaml` → 🧊 新加坡专线

- 子串匹配：`binance` `facebook` `fbcdn` `huobi` `metamask`
- 短关键词（3 个字符）：`okx`

`clash-classic/Telegram-classic.yaml` → 🛸 Telegram

- 子串匹配：`nicegram`

`clash-classic/TikTok-classic.yaml` → 📱 TikTok

- 子串匹配：`musical.ly` `tiktok`

`clash-classic/YouTube-classic.yaml` → 💻 YouTube

- 子串匹配：`youtube`

## 已发布：整个公共后缀（206）

`clash-domain/AI.yaml` → 🗨️ ChatGPT

- 覆盖公共后缀 .bing 下的域名：`+.bing`

`clash-domain/America.yaml` → ⛳ 美国专线

- 覆盖公共后缀 .android 下的域名：`+.android`
- 覆盖公共后缀 .java 下的域名：`+.java`
- 覆盖公共后缀 .mit 下的域名：`+.mit`
- 手写 · 覆盖公共后缀 .us 下的域名：`+.us`
- 覆盖公共后缀 .ac.ir 下的域名：`+.ac.ir`
- 覆盖公共后缀 .ac.uk 下的域名：`+.ac.uk`
- 覆盖公共后缀 .edu.hk 下的域名：`+.edu.hk`
- 覆盖公共后缀 .xn--wcvs22d.xn--j6w193g 下的域名：`+.xn--wcvs22d.xn--j6w193g`

`clash-domain/Apple.yaml` → 🍎 Apple

- 覆盖公共后缀 .apple 下的域名：`+.apple`

`clash-domain/China.yaml` → DIRECT

- 覆盖公共后缀 .alibaba 下的域名：`+.alibaba`
- 覆盖公共后缀 .alipay 下的域名：`+.alipay`
- 覆盖公共后缀 .anquan 下的域名：`+.anquan`
- 覆盖公共后缀 .baidu 下的域名：`+.baidu`
- 覆盖公共后缀 .citic 下的域名：`+.citic`
- 手写 · 覆盖公共后缀 .cn 下的域名：`+.cn`
- 覆盖公共后缀 .full 下的域名：`+.full`
- 覆盖公共后缀 .icbc 下的域名：`+.icbc`
- 覆盖公共后缀 .ms 下的域名：`+.ms`
- 覆盖公共后缀 .shouji 下的域名：`+.shouji`
- 覆盖公共后缀 .sina 下的域名：`+.sina`
- 覆盖公共后缀 .sohu 下的域名：`+.sohu`
- 覆盖公共后缀 .taobao 下的域名：`+.taobao`
- 覆盖公共后缀 .tmall 下的域名：`+.tmall`
- 覆盖公共后缀 .unicom 下的域名：`+.unicom`
- 覆盖公共后缀 .wang 下的域名：`+.wang`
- 覆盖公共后缀 .weibo 下的域名：`+.weibo`
- 覆盖公共后缀 .xihuan 下的域名：`+.xihuan`
- 覆盖公共后缀 .xn--1qqw23a 下的域名：`+.xn--1qqw23a`
- 覆盖公共后缀 .xn--3bst00m 下的域名：`+.xn--3bst00m`
- 覆盖公共后缀 .xn--3ds443g 下的域名：`+.xn--3ds443g`
- 覆盖公共后缀 .xn--55qw42g 下的域名：`+.xn--55qw42g`
- 覆盖公共后缀 .xn--55qx5d 下的域名：`+.xn--55qx5d`
- 覆盖公共后缀 .xn--5tzm5g 下的域名：`+.xn--5tzm5g`
- 覆盖公共后缀 .xn--6frz82g 下的域名：`+.xn--6frz82g`
- 覆盖公共后缀 .xn--6qq986b3xl 下的域名：`+.xn--6qq986b3xl`
- 覆盖公共后缀 .xn--8y0a063a 下的域名：`+.xn--8y0a063a`
- 覆盖公共后缀 .xn--9et52u 下的域名：`+.xn--9et52u`
- 覆盖公共后缀 .xn--9krt00a 下的域名：`+.xn--9krt00a`
- 覆盖公共后缀 .xn--czr694b 下的域名：`+.xn--czr694b`
- 覆盖公共后缀 .xn--czrs0t 下的域名：`+.xn--czrs0t`
- 覆盖公共后缀 .xn--czru2d 下的域名：`+.xn--czru2d`
- 覆盖公共后缀 .xn--fiq228c5hs 下的域名：`+.xn--fiq228c5hs`
- 覆盖公共后缀 .xn--fiq64b 下的域名：`+.xn--fiq64b`
- 覆盖公共后缀 .xn--fiqs8s 下的域名：`+.xn--fiqs8s`
- 覆盖公共后缀 .xn--fiqz9s 下的域名：`+.xn--fiqz9s`
- 覆盖公共后缀 .xn--fjq720a 下的域名：`+.xn--fjq720a`
- 覆盖公共后缀 .xn--g2xx48c 下的域名：`+.xn--g2xx48c`
- 覆盖公共后缀 .xn--hxt814e 下的域名：`+.xn--hxt814e`
- 覆盖公共后缀 .xn--imr513n 下的域名：`+.xn--imr513n`
- 覆盖公共后缀 .xn--io0a7i 下的域名：`+.xn--io0a7i`
- 覆盖公共后缀 .xn--kput3i 下的域名：`+.xn--kput3i`
- 覆盖公共后缀 .xn--nyqy26a 下的域名：`+.xn--nyqy26a`
- 覆盖公共后缀 .xn--otu796d 下的域名：`+.xn--otu796d`
- 覆盖公共后缀 .xn--rhqv96g 下的域名：`+.xn--rhqv96g`
- 覆盖公共后缀 .xn--ses554g 下的域名：`+.xn--ses554g`
- 覆盖公共后缀 .xn--unup4y 下的域名：`+.xn--unup4y`
- 覆盖公共后缀 .xn--vhquv 下的域名：`+.xn--vhquv`
- 覆盖公共后缀 .xn--vuq861b 下的域名：`+.xn--vuq861b`
- 覆盖公共后缀 .xn--xhq521b 下的域名：`+.xn--xhq521b`
- 覆盖公共后缀 .xn--zfr164b 下的域名：`+.xn--zfr164b`
- 覆盖公共后缀 .yun 下的域名：`+.yun`
- 覆盖公共后缀 .in.th 下的域名：`+.in.th`

`clash-domain/ChinaMedia.yaml` → DIRECT

- 覆盖公共后缀 .alibaba 下的域名：`+.alibaba`
- 覆盖公共后缀 .alipay 下的域名：`+.alipay`
- 覆盖公共后缀 .baidu 下的域名：`+.baidu`
- 覆盖公共后缀 .playstation 下的域名：`+.playstation`
- 覆盖公共后缀 .sohu 下的域名：`+.sohu`
- 覆盖公共后缀 .taobao 下的域名：`+.taobao`
- 覆盖公共后缀 .tmall 下的域名：`+.tmall`
- 覆盖公共后缀 .unicom 下的域名：`+.unicom`
- 覆盖公共后缀 .xbox 下的域名：`+.xbox`
- 覆盖公共后缀 .xn--8y0a063a 下的域名：`+.xn--8y0a063a`

`clash-domain/Direct.yaml` → DIRECT

- 覆盖公共后缀 .java 下的域名：`+.java`
- 覆盖公共后缀 .oracle 下的域名：`+.oracle`
- 覆盖公共后缀 .home.arpa 下的域名：`+.home.arpa`

`clash-domain/Google.yaml` → 📩 Google

- 覆盖公共后缀 .android 下的域名：`+.android`
- 覆盖公共后缀 .chrome 下的域名：`+.chrome`
- 覆盖公共后缀 .dclk 下的域名：`+.dclk`
- 覆盖公共后缀 .gbiz 下的域名：`+.gbiz`
- 覆盖公共后缀 .gle 下的域名：`+.gle`
- 覆盖公共后缀 .gmail 下的域名：`+.gmail`
- 覆盖公共后缀 .goog 下的域名：`+.goog`
- 覆盖公共后缀 .google 下的域名：`+.google`
- 覆盖公共后缀 .guge 下的域名：`+.guge`
- 覆盖公共后缀 .hangout 下的域名：`+.hangout`
- 覆盖公共后缀 .nexus 下的域名：`+.nexus`
- 覆盖公共后缀 .xn--flw351e 下的域名：`+.xn--flw351e`
- 覆盖公共后缀 .xn--qcka1pmc 下的域名：`+.xn--qcka1pmc`
- 覆盖公共后缀 .youtube 下的域名：`+.youtube`

`clash-domain/HK.yaml` → 🛫 香港专线

- 覆盖公共后缀 .azure 下的域名：`+.azure`
- 手写 · 覆盖公共后缀 .hk 下的域名：`+.hk`
- 覆盖公共后缀 .playstation 下的域名：`+.playstation`
- 覆盖公共后缀 .xbox 下的域名：`+.xbox`

`clash-domain/Japan.yaml` → 🌺 日本专线

- 覆盖公共后缀 .amazon 下的域名：`+.amazon`
- 覆盖公共后缀 .aws 下的域名：`+.aws`
- 覆盖公共后缀 .imdb 下的域名：`+.imdb`
- 手写 · 覆盖公共后缀 .jp 下的域名：`+.jp`
- 覆盖公共后缀 .kindle 下的域名：`+.kindle`
- 覆盖公共后缀 .nico 下的域名：`+.nico`
- 覆盖公共后缀 .xn--cckwcxetd 下的域名：`+.xn--cckwcxetd`
- 覆盖公共后缀 .xn--jlq480n2rg 下的域名：`+.xn--jlq480n2rg`
- 覆盖公共后缀 .yamaxun 下的域名：`+.yamaxun`
- 覆盖公共后缀 .zappos 下的域名：`+.zappos`

`clash-domain/Media.yaml` → 🛖 国际流媒体

- 覆盖公共后缀 .adult 下的域名：`+.adult`
- 覆盖公共后缀 .bbc 下的域名：`+.bbc`
- 覆盖公共后缀 .bloomberg 下的域名：`+.bloomberg`
- 覆盖公共后缀 .fox 下的域名：`+.fox`
- 覆盖公共后缀 .nhk 下的域名：`+.nhk`
- 覆盖公共后缀 .porn 下的域名：`+.porn`
- 覆盖公共后缀 .sky 下的域名：`+.sky`
- 覆盖公共后缀 .youtube 下的域名：`+.youtube`

`clash-domain/Microsoft.yaml` → 🪟 Microsoft

- 覆盖公共后缀 .azure 下的域名：`+.azure`
- 覆盖公共后缀 .bing 下的域名：`+.bing`
- 覆盖公共后缀 .hotmail 下的域名：`+.hotmail`
- 覆盖公共后缀 .microsoft 下的域名：`+.microsoft`
- 覆盖公共后缀 .office 下的域名：`+.office`
- 覆盖公共后缀 .onedrive 下的域名：`+.onedrive`
- 覆盖公共后缀 .onedriveupdater 下的域名：`+.onedriveupdater`
- 覆盖公共后缀 .skype 下的域名：`+.skype`
- 覆盖公共后缀 .windows 下的域名：`+.windows`
- 覆盖公共后缀 .xbox 下的域名：`+.xbox`

`clash-domain/OneDrive.yaml` → ⛅ OneDrive

- 覆盖公共后缀 .onedrive 下的域名：`+.onedrive`
- 覆盖公共后缀 .onedriveupdater 下的域名：`+.onedriveupdater`

`clash-domain/Proxy.yaml` → 🌠 节点选择

- 覆盖公共后缀 .adult 下的域名：`+.adult`
- 覆盖公共后缀 .amazon 下的域名：`+.amazon`
- 覆盖公共后缀 .android 下的域名：`+.android`
- 覆盖公共后缀 .apple 下的域名：`+.apple`
- 覆盖公共后缀 .aws 下的域名：`+.aws`
- 覆盖公共后缀 .azure 下的域名：`+.azure`
- 覆盖公共后缀 .bbc 下的域名：`+.bbc`
- 覆盖公共后缀 .bing 下的域名：`+.bing`
- 覆盖公共后缀 .bloomberg 下的域名：`+.bloomberg`
- 覆盖公共后缀 .bmw 下的域名：`+.bmw`
- 覆盖公共后缀 .bridgestone 下的域名：`+.bridgestone`
- 覆盖公共后缀 .canon 下的域名：`+.canon`
- 覆盖公共后缀 .cern 下的域名：`+.cern`
- 覆盖公共后缀 .chrome 下的域名：`+.chrome`
- 覆盖公共后缀 .cisco 下的域名：`+.cisco`
- 覆盖公共后缀 .dclk 下的域名：`+.dclk`
- 覆盖公共后缀 .dell 下的域名：`+.dell`
- 覆盖公共后缀 .flickr 下的域名：`+.flickr`
- 覆盖公共后缀 .fox 下的域名：`+.fox`
- 覆盖公共后缀 .gbiz 下的域名：`+.gbiz`
- 覆盖公共后缀 .gle 下的域名：`+.gle`
- 覆盖公共后缀 .gmail 下的域名：`+.gmail`
- 覆盖公共后缀 .gmo 下的域名：`+.gmo`
- 覆盖公共后缀 .godaddy 下的域名：`+.godaddy`
- 覆盖公共后缀 .goog 下的域名：`+.goog`
- 覆盖公共后缀 .google 下的域名：`+.google`
- 覆盖公共后缀 .gucci 下的域名：`+.gucci`
- 覆盖公共后缀 .guge 下的域名：`+.guge`
- 覆盖公共后缀 .hangout 下的域名：`+.hangout`
- 覆盖公共后缀 .hbo 下的域名：`+.hbo`
- 覆盖公共后缀 .hotmail 下的域名：`+.hotmail`
- 覆盖公共后缀 .hsbc 下的域名：`+.hsbc`
- 覆盖公共后缀 .ibm 下的域名：`+.ibm`
- 覆盖公共后缀 .imdb 下的域名：`+.imdb`
- 覆盖公共后缀 .intuit 下的域名：`+.intuit`
- 覆盖公共后缀 .java 下的域名：`+.java`
- 覆盖公共后缀 .kindle 下的域名：`+.kindle`
- 覆盖公共后缀 .microsoft 下的域名：`+.microsoft`
- 覆盖公共后缀 .mini 下的域名：`+.mini`
- 覆盖公共后缀 .mit 下的域名：`+.mit`
- 覆盖公共后缀 .nexus 下的域名：`+.nexus`
- 覆盖公共后缀 .nhk 下的域名：`+.nhk`
- 覆盖公共后缀 .nico 下的域名：`+.nico`
- 覆盖公共后缀 .nike 下的域名：`+.nike`
- 覆盖公共后缀 .office 下的域名：`+.office`
- 覆盖公共后缀 .oracle 下的域名：`+.oracle`
- 覆盖公共后缀 .panasonic 下的域名：`+.panasonic`
- 覆盖公共后缀 .playstation 下的域名：`+.playstation`
- 覆盖公共后缀 .porn 下的域名：`+.porn`
- 覆盖公共后缀 .samsung 下的域名：`+.samsung`
- 覆盖公共后缀 .sky 下的域名：`+.sky`
- 覆盖公共后缀 .skype 下的域名：`+.skype`
- 覆盖公共后缀 .softbank 下的域名：`+.softbank`
- 覆盖公共后缀 .sony 下的域名：`+.sony`
- 覆盖公共后缀 .target 下的域名：`+.target`
- 覆盖公共后缀 .volvo 下的域名：`+.volvo`
- 覆盖公共后缀 .walmart 下的域名：`+.walmart`
- 覆盖公共后缀 .weather 下的域名：`+.weather`
- 覆盖公共后缀 .weatherchannel 下的域名：`+.weatherchannel`
- 覆盖公共后缀 .windows 下的域名：`+.windows`
- 覆盖公共后缀 .xbox 下的域名：`+.xbox`
- 覆盖公共后缀 .xn--cckwcxetd 下的域名：`+.xn--cckwcxetd`
- 覆盖公共后缀 .xn--cg4bki 下的域名：`+.xn--cg4bki`
- 覆盖公共后缀 .xn--flw351e 下的域名：`+.xn--flw351e`
- 覆盖公共后缀 .xn--jlq480n2rg 下的域名：`+.xn--jlq480n2rg`
- 覆盖公共后缀 .xn--qcka1pmc 下的域名：`+.xn--qcka1pmc`
- 覆盖公共后缀 .yahoo 下的域名：`+.yahoo`
- 覆盖公共后缀 .yamaxun 下的域名：`+.yamaxun`
- 覆盖公共后缀 .yandex 下的域名：`+.yandex`
- 覆盖公共后缀 .youtube 下的域名：`+.youtube`
- 覆盖公共后缀 .zappos 下的域名：`+.zappos`
- 覆盖公共后缀 .ac.ir 下的域名：`+.ac.ir`
- 覆盖公共后缀 .ac.uk 下的域名：`+.ac.uk`
- 覆盖公共后缀 .edu.hk 下的域名：`+.edu.hk`
- 覆盖公共后缀 .go.jp 下的域名：`+.go.jp`
- 覆盖公共后缀 .gov.ir 下的域名：`+.gov.ir`
- 覆盖公共后缀 .gov.tw 下的域名：`+.gov.tw`
- 覆盖公共后缀 .idv.tw 下的域名：`+.idv.tw`
- 覆盖公共后缀 .xn--wcvs22d.xn--j6w193g 下的域名：`+.xn--wcvs22d.xn--j6w193g`

`clash-domain/Singapore.yaml` → 🧊 新加坡专线

- 手写 · 覆盖公共后缀 .sg 下的域名：`+.sg`

`clash-domain/Tencent.yaml` → DIRECT

- 覆盖公共后缀 .in.th 下的域名：`+.in.th`

`clash-domain/YouTube.yaml` → 💻 YouTube

- 覆盖公共后缀 .youtube 下的域名：`+.youtube`

## 已发布：大网段（1）

`clash-ipcidr/Apple-ipcidr.yaml` → 🍎 Apple

- /8 大网段：`17.0.0.0/8`

## 已发布：IP-ASN（10）

`clash-classic/AI-classic.yaml` → 🗨️ ChatGPT

- 整个自治系统的地址：`14061,no-resolve` `20473,no-resolve`

`clash-classic/China-classic.yaml` → DIRECT

- 整个自治系统的地址：`132203,no-resolve`

`clash-classic/Singapore-classic.yaml` → 🧊 新加坡专线

- 整个自治系统的地址：`32934,no-resolve`

`clash-classic/Telegram-classic.yaml` → 🛸 Telegram

- 整个自治系统的地址：`211157,no-resolve` `44907,no-resolve` `59930,no-resolve` `62014,no-resolve` `62041,no-resolve`

`clash-classic/Tencent-classic.yaml` → DIRECT

- 整个自治系统的地址：`132203,no-resolve`

## 已发布：GEOIP / GEOSITE（3）

`clash-classic/China-classic.yaml` → DIRECT

- 手写 · 整个国家/地区或站点分类：`GEOSITE,geolocation-cn`

`clash-classic/Proxy-classic.yaml` → 🌠 节点选择

- 手写 · 整个国家/地区或站点分类：`GEOSITE,geolocation-!cn` `GEOSITE,geolocation-cn@!cn`

## 已发布：进程与用户（155）

`clash-classic/America-classic.yaml` → ⛳ 美国专线

- 该程序的全部流量：`PROCESS-NAME,com.cbs.app` `PROCESS-NAME,com.hulu.plus` `PROCESS-NAME,com.showtime.standalone`

`clash-classic/Apple-classic.yaml` → 🍎 Apple

- 该程序的全部流量：`PROCESS-NAME,CoreLocationAgent` `PROCESS-NAME,LookupViewService` `PROCESS-NAME,Music` `PROCESS-NAME,TV` `PROCESS-NAME,WeatherWidget` `PROCESS-NAME,apsd` `PROCESS-NAME,com.apple.Maps` `PROCESS-NAME,com.apple.geod` `PROCESS-NAME,findmydevice-user-agent` `PROCESS-NAME,fmfd` `PROCESS-NAME,mapspushd` `PROCESS-NAME,netbiosd` `PROCESS-NAME,trustd`

`clash-classic/Bilibili-classic.yaml` → 📺 哔哩哔哩

- 该程序的全部流量：`PROCESS-NAME,com.bilibili.app.blue` `PROCESS-NAME,com.bilibili.app.in` `PROCESS-NAME,com.bilibili.comic` `PROCESS-NAME,com.bilibili.comic.intl` `PROCESS-NAME,com.zhiliaoapp.musically` `PROCESS-NAME,tv.danmaku.bili` `PROCESS-NAME,tv.danmaku.bilibilihd`

`clash-classic/China-classic.yaml` → DIRECT

- 该程序的全部流量：`PROCESS-NAME,BaiduNetdisk_mac` `PROCESS-NAME,BitComet` `PROCESS-NAME,ClashX` `PROCESS-NAME,DownloadService` `PROCESS-NAME,Folx` `PROCESS-NAME,LocalSend` `PROCESS-NAME,LogiOptions` `PROCESS-NAME,LogiOptionsDaemon` `PROCESS-NAME,NetTransport` `PROCESS-NAME,SunloginClient_Desktop` `PROCESS-NAME,SunloginClient_Helper` `PROCESS-NAME,Thunder` `PROCESS-NAME,Thunder.exe` `PROCESS-NAME,ThunderVIP` `PROCESS-NAME,Transmission` `PROCESS-NAME,UUBooster` `PROCESS-NAME,WebTorrent` `PROCESS-NAME,WebTorrentHelper` `PROCESS-NAME,amuled` `PROCESS-NAME,aria2c` `PROCESS-NAME,clash` `PROCESS-NAME,cloudflared` `PROCESS-NAME,com.bilibili.app.blue` `PROCESS-NAME,com.bilibili.app.in` `PROCESS-NAME,com.bilibili.comic` `PROCESS-NAME,com.bilibili.comic.intl` `PROCESS-NAME,com.jjwxc.reader` `PROCESS-NAME,com.qiyi.video` `PROCESS-NAME,com.taobao.taobao` `PROCESS-NAME,com.xiaomi.mibrain.speech` `PROCESS-NAME,com.zhiliaoapp.musically` `PROCESS-NAME,fdm` `PROCESS-NAME,parsecd` `PROCESS-NAME,privoxy` `PROCESS-NAME,qBittorrent` `PROCESS-NAME,qbittorrent*` `PROCESS-NAME,qbittorrent-nox` `PROCESS-NAME,ss-local` `PROCESS-NAME,tailscaled` `PROCESS-NAME,transmission-daemon` `PROCESS-NAME,transmission-qt` `PROCESS-NAME,trojan` `PROCESS-NAME,trojan-go` `PROCESS-NAME,tv.danmaku.bili` `PROCESS-NAME,tv.danmaku.bilibilihd` `PROCESS-NAME,uTorrent` `PROCESS-NAME,v2ray` `PROCESS-NAME,xray` `PROCESS-NAME,小米云服务.exe`

`clash-classic/ChinaMedia-classic.yaml` → DIRECT

- 该程序的全部流量：`PROCESS-NAME,com.bilibili.app.blue` `PROCESS-NAME,com.bilibili.app.in` `PROCESS-NAME,com.bilibili.comic` `PROCESS-NAME,com.bilibili.comic.intl` `PROCESS-NAME,com.taobao.taobao` `PROCESS-NAME,com.xiaomi.mibrain.speech` `PROCESS-NAME,tv.danmaku.bili` `PROCESS-NAME,tv.danmaku.bilibilihd` `PROCESS-NAME,小米云服务.exe`

`clash-classic/Direct-classic.yaml` → DIRECT

- 该程序的全部流量：`PROCESS-NAME,BitComet` `PROCESS-NAME,BitComet.exe` `PROCESS-NAME,BitComet_x64.exe` `PROCESS-NAME,CrashReport.exe` `PROCESS-NAME,DownloadService` `PROCESS-NAME,DownloadService.exe` `PROCESS-NAME,DriverInstaller.exe` `PROCESS-NAME,Folx` `PROCESS-NAME,Folx.exe` `PROCESS-NAME,NetTransport` `PROCESS-NAME,NetTransport.exe` `PROCESS-NAME,SunloginClient.exe` `PROCESS-NAME,Thunder` `PROCESS-NAME,Thunder.exe` `PROCESS-NAME,ToDesk.exe` `PROCESS-NAME,ToDesk_Service.exe` `PROCESS-NAME,ToDesk_Session.exe` `PROCESS-NAME,ToDesk_Setup.exe` `PROCESS-NAME,Transmission` `PROCESS-NAME,Transmission.exe` `PROCESS-NAME,WebTorrent` `PROCESS-NAME,WebTorrent.exe` `PROCESS-NAME,WebTorrentHelper` `PROCESS-NAME,WebTorrentHelper.exe` `PROCESS-NAME,Weiyun` `PROCESS-NAME,Weiyun.exe` `PROCESS-NAME,aria2c` `PROCESS-NAME,aria2c.exe` `PROCESS-NAME,baidunetdisk.exe` `PROCESS-NAME,devcon.exe` `PROCESS-NAME,fdm` `PROCESS-NAME,fdm.exe` `PROCESS-NAME,mstsc.exe` `PROCESS-NAME,qbittorrent` `PROCESS-NAME,qbittorrent.exe` `PROCESS-NAME,uTorrent` `PROCESS-NAME,uTorrent.exe`

`clash-classic/Google-classic.yaml` → 📩 Google

- 该程序的全部流量：`PROCESS-NAME,BackupandSync` `PROCESS-NAME,GoogleDriveFS.exe` `PROCESS-NAME,com.android.vending` `PROCESS-NAME,com.google.android.gms` `PROCESS-NAME,com.google.android.gsf` `PROCESS-NAME,com.google.android.play.games`

`clash-classic/Japan-classic.yaml` → 🌺 日本专线

- 该程序的全部流量：`PROCESS-NAME,com.amazon.avod.thirdpartyclient` `PROCESS-NAME,com.spotify.music`

`clash-classic/Media-classic.yaml` → 🛖 国际流媒体

- 该程序的全部流量：`PROCESS-NAME,com.amazon.avod.thirdpartyclient` `PROCESS-NAME,com.bstar.intl` `PROCESS-NAME,com.disney.datg.videoplatforms.android.abc` `PROCESS-NAME,com.disney.disneyplus` `PROCESS-NAME,com.hktve.viutv` `PROCESS-NAME,com.hulu.plus` `PROCESS-NAME,com.linecorp.linetv` `PROCESS-NAME,com.netflix.mediaclient` `PROCESS-NAME,com.tencent.ibg.joox` `PROCESS-NAME,com.twgood.android` `PROCESS-NAME,com.viu.pad` `PROCESS-NAME,com.viu.phone` `PROCESS-NAME,com.vuclip.viu` `PROCESS-NAME,music` `PROCESS-NAME,tv` `PROCESS-NAME,tv.twitch.android.app`

`clash-classic/Microsoft-classic.yaml` → 🪟 Microsoft

- 该程序的全部流量：`PROCESS-NAME,OneDrive` `PROCESS-NAME,OneDriveUpdater`

`clash-classic/Netflix-classic.yaml` → 🎬 Netflix

- 该程序的全部流量：`PROCESS-NAME,com.netflix.mediaclient`

`clash-classic/OneDrive-classic.yaml` → ⛅ OneDrive

- 该程序的全部流量：`PROCESS-NAME,OneDrive` `PROCESS-NAME,OneDriveUpdater`

`clash-classic/Proxy-classic.yaml` → 🌠 节点选择

- 该程序的全部流量：`PROCESS-NAME,LookupViewService`

`clash-classic/Telegram-classic.yaml` → 🛸 Telegram

- 该程序的全部流量：`PROCESS-NAME,Telegram.exe` `PROCESS-NAME,nekox.messenger` `PROCESS-NAME,org.telegram.messenger` `PROCESS-NAME,telegram-desktop` `PROCESS-NAME,tw.nekomimi.nekogram` `PROCESS-NAME,xyz.nextalone.nagram`

`clash-classic/TikTok-classic.yaml` → 📱 TikTok

- 该程序的全部流量：`PROCESS-NAME,com.zhiliaoapp.musically`

## 已发布：连接属性（2）

`clash-classic/Direct-classic.yaml` → DIRECT

- 手写 · 不区分目标，按连接属性匹配：`DST-PORT,9993` `SRC-PORT,9993`
