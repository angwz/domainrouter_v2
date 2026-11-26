# 规则更新说明

- 生成时间（UTC）：2026-11-26T11:40:32+00:00
- generation：`de7af85cbcf0379e`
- 结果：有变化，已更新发布文件

## 宽泛规则

本次过滤上游规则 0 条，新发布的宽泛规则 1 条。完整清单见 [broad-rules.md](broad-rules.md)。

| 新发布 | 说明 | 文件 |
| --- | --- | --- |
| `DOMAIN-KEYWORD,paypal` | 子串匹配 | `clash-classic/America-classic.yaml` |

## 来源

共 210 个：正常 210 个，失败 0 个（使用旧副本）。

## 规则变化

| 文件 | 条目 | 新增 | 删除 |
| --- | --- | --- | --- |
| `clash-classic/America-classic.yaml` | 4 → 5 | 1 | 0 |
| `clash-classic/HK-classic.yaml` | 6 → 5 | 0 | 1 |
| `clash-domain/AI.yaml` | 310 → 308 | 0 | 2 |
| `clash-domain/America.yaml` | 1694 → 1934 | 240 | 0 |
| `clash-domain/HK.yaml` | 1307 → 1063 | 0 | 244 |
| `clash-domain/Proxy.yaml` | 29902 → 29913 | 11 | 0 |
| `clash-ipcidr/China-ipcidr.yaml` | 12571 → 12584 | 13 | 0 |
| `clash-ipcidr/Google-ipcidr.yaml` | 7090 → 6915 | 137 | 312 |
| `clash-ipcidr/Singapore-ipcidr.yaml` | 141 → 141 | 2 | 2 |

<details>
<summary><code>clash-classic/America-classic.yaml</code></summary>

新增（1）：

```text
DOMAIN-KEYWORD,paypal
```

</details>

<details>
<summary><code>clash-classic/HK-classic.yaml</code></summary>

删除（1）：

```text
DOMAIN-KEYWORD,paypal
```

</details>

<details>
<summary><code>clash-domain/AI.yaml</code></summary>

删除（2）：

```text
+.ovh.us
+.us.ovhcloud.com
```

</details>

<details>
<summary><code>clash-domain/America.yaml</code></summary>

新增（240）：

```text
+.account-paypal.info
+.account-paypal.net
+.account-paypal.org
+.accountpaypal.com
+.accountpaypal.net
+.accountpaypal.org
+.anfutong.cn
+.anfutong.com
+.anfutong.com.cn
+.beibao.cn
+.beibao.com
+.beibao.com.cn
+.bill-safe.com
+.billmelater.com
+.billmelater.info
+.billmelater.net
+.bml.info
+.braintreegateway.com
+.braintreegateway.tv
+.braintreepayments.com
+.braintreepayments.info
+.braintreepayments.org
+.braintreepayments.tv
+.braintreepaymentsolutions.com
+.braintreeps.com
+.briantreepayments.net
+.briantreepayments.tv
+.buyfast-paysmart.net
+.card.io
+.cash2.com
+.cashify.com
+.cashify.net
+.devtools-paypal.com
+.experiencebillmelater.com
+.filipino-music.net
+.fundpaypal.com
+.getbraintree.com
+.gmoney.org
+.i-o-u.info
+.krakenjs.com
+.loanbuilder.com
+.login-paypal.com
+.login-paypal.info
+.mywaytopay.info
+.mywaytopay.net
+.pa9pal.com
+.paaypal.com
+.paily.net
+.paily.org
+.paipal.com
+.pavpal.com
+.paydiant.com
+.paylike.com
+.paypa1.com
+.paypa1.org
+.paypaal.com
+.paypal-activate.com
+.paypal-activate.info
+.paypal-activate.org
+.paypal-apac.com
+.paypal-apps.com
+.paypal-biz.com
+.paypal-brandcentral.com
+.paypal-business.com
+.paypal-business.net
+.paypal-business.org
+.paypal-cardcash.com
+.paypal-cash.com
+.paypal-center.com
+.paypal-center.info
+.paypal-center.net
+.paypal-center.org
+.paypal-communication.com
+.paypal-communications.com
+.paypal-communications.net
+.paypal-community.com
+.paypal-community.net
+.paypal-comunidad.com
+.paypal-corp.com
+.paypal-database.com
+.paypal-donations.com
+.paypal-dynamic.com
+.paypal-engineering.com
+.paypal-europe.com
+.paypal-excelinvoicing.com
+.paypal-exchanges.com
+.paypal-forward.com
+.paypal-galactic.com
+.paypal-gift.com
+.paypal-gifts.com
+.paypal-gpplus.com
+.paypal-here.com
+.paypal-hrsystem.com
+.paypal-innovationlab.com
+.paypal-integration.com
+.paypal-japan.com
+.paypal-knowledge.com
+.paypal-labs.com
+.paypal-latam.com
+.paypal-learning.com
+.paypal-login.com
+.paypal-login.info
+.paypal-login.org
+.paypal-luxury.com
+.paypal-mainstreet.net
+.paypal-marketing.com
+.paypal-media.com
+.paypal-merchantloyalty.com
+.paypal-mktg.com
+.paypal-mobilemoney.com
+.paypal-network.org
+.paypal-notice.com
+.paypal-notify.com
+.paypal-online.info
+.paypal-online.net
+.paypal-online.org
+.paypal-optimizer.com
+.paypal-pages.com
+.paypal-photocard.com
+.paypal-plaza.com
+.paypal-portal.com
+.paypal-prepagata.com
+.paypal-prepagata.net
+.paypal-prepaid.com
+.paypal-profile.com
+.paypal-proserv.com
+.paypal-qrshopping.org
+.paypal-recargacelular.com
+.paypal-redeem.com
+.paypal-referral.com
+.paypal-retail.com
+.paypal-scoop.com
+.paypal-search.com
+.paypal-secure.net
+.paypal-secure.org
+.paypal-security.net
+.paypal-security.org
+.paypal-service.org
+.paypal-signin.com
+.paypal-special.com
+.paypal-specialoffers.com
+.paypal-sptam.com
+.paypal-status.com
+.paypal-support.com
+.paypal-survey.com
+.paypal-survey.org
+.paypal-team.com
+.paypal-viewpoints.net
+.paypal.ca
+.paypal.com
+.paypal.com.cn
+.paypal.com.hk
+.paypal.com.sg
+.paypal.hk
+.paypal.info
+.paypal.jp
+.paypal.me
+.paypal.net.cn
+.paypal.org.cn
+.paypal.so
+.paypalbeacon.com
+.paypalbenefits.com
+.paypalbrasil.com
+.paypalcommunity.cn
+.paypalcommunity.com
+.paypalcommunity.net
+.paypalcommunity.org
+.paypalcorp.com
+.paypalcredit.com
+.paypalcreditcard.com
+.paypalgivingfund.org
+.paypalhere.cn
+.paypalhere.com
+.paypalhere.com.cn
+.paypalhere.info
+.paypalhere.net
+.paypalhere.org
+.paypalhere.tv
+.paypali.net
+.paypalinc.com
+.paypalindia.com
+.paypalinsuranceservices.org
+.paypall.com
+.paypallabs.com
+.paypalme.com
+.paypalnet.net
+.paypalnet.org
+.paypalnetwork.info
+.paypalnetwork.net
+.paypalnetwork.org
+.paypalobjects.com
+.paypalonline.net
+.paypalonline.org
+.paypalprepagata.com
+.paypalprepagata.net
+.paypalservice.com
+.paypalshopping.com
+.paypalshopping.net
+.paypalsurvey.com
+.paypalx.com
```
……其余 40 条见 changes.json

</details>

<details>
<summary><code>clash-domain/HK.yaml</code></summary>

删除（244）：

```text
+.account-paypal.info
+.account-paypal.net
+.account-paypal.org
+.accountpaypal.com
+.accountpaypal.net
+.accountpaypal.org
+.anfutong.cn
+.anfutong.com
+.anfutong.com.cn
+.beibao.cn
+.beibao.com
+.beibao.com.cn
+.bill-safe.com
+.billmelater.com
+.billmelater.info
+.billmelater.net
+.bml.info
+.braintreegateway.com
+.braintreegateway.tv
+.braintreepayments.com
+.braintreepayments.info
+.braintreepayments.org
+.braintreepayments.tv
+.braintreepaymentsolutions.com
+.braintreeps.com
+.briantreepayments.net
+.briantreepayments.tv
+.buyfast-paysmart.net
+.card.io
+.cash2.com
+.cashify.com
+.cashify.net
+.devtools-paypal.com
+.experiencebillmelater.com
+.filipino-music.net
+.fundpaypal.com
+.getbraintree.com
+.gmoney.org
+.i-o-u.info
+.krakenjs.com
+.loanbuilder.com
+.login-paypal.com
+.login-paypal.info
+.mywaytopay.info
+.mywaytopay.net
+.pa9pal.com
+.paaypal.com
+.paily.net
+.paily.org
+.paipal.com
+.pavpal.com
+.paydiant.com
+.paylike.com
+.paypa1.com
+.paypa1.org
+.paypaal.com
+.paypal-activate.com
+.paypal-activate.info
+.paypal-activate.org
+.paypal-apac.com
+.paypal-apps.com
+.paypal-biz.com
+.paypal-brandcentral.com
+.paypal-business.com
+.paypal-business.net
+.paypal-business.org
+.paypal-cardcash.com
+.paypal-cash.com
+.paypal-center.com
+.paypal-center.info
+.paypal-center.net
+.paypal-center.org
+.paypal-communication.com
+.paypal-communications.com
+.paypal-communications.net
+.paypal-community.com
+.paypal-community.net
+.paypal-comunidad.com
+.paypal-corp.com
+.paypal-database.com
+.paypal-database.us
+.paypal-donations.com
+.paypal-dynamic.com
+.paypal-engineering.com
+.paypal-europe.com
+.paypal-excelinvoicing.com
+.paypal-exchanges.com
+.paypal-forward.com
+.paypal-galactic.com
+.paypal-gift.com
+.paypal-gifts.com
+.paypal-gpplus.com
+.paypal-here.com
+.paypal-hrsystem.com
+.paypal-innovationlab.com
+.paypal-integration.com
+.paypal-japan.com
+.paypal-knowledge.com
+.paypal-labs.com
+.paypal-latam.com
+.paypal-learning.com
+.paypal-login.com
+.paypal-login.info
+.paypal-login.org
+.paypal-login.us
+.paypal-luxury.com
+.paypal-mainstreet.net
+.paypal-marketing.com
+.paypal-media.com
+.paypal-merchantloyalty.com
+.paypal-mktg.com
+.paypal-mobilemoney.com
+.paypal-network.org
+.paypal-notice.com
+.paypal-notify.com
+.paypal-online.info
+.paypal-online.net
+.paypal-online.org
+.paypal-optimizer.com
+.paypal-pages.com
+.paypal-photocard.com
+.paypal-plaza.com
+.paypal-portal.com
+.paypal-prepagata.com
+.paypal-prepagata.net
+.paypal-prepaid.com
+.paypal-profile.com
+.paypal-proserv.com
+.paypal-qrshopping.org
+.paypal-recargacelular.com
+.paypal-redeem.com
+.paypal-referral.com
+.paypal-retail.com
+.paypal-scoop.com
+.paypal-search.com
+.paypal-secure.net
+.paypal-secure.org
+.paypal-security.net
+.paypal-security.org
+.paypal-service.org
+.paypal-signin.com
+.paypal-signin.us
+.paypal-special.com
+.paypal-specialoffers.com
+.paypal-sptam.com
+.paypal-status.com
+.paypal-support.com
+.paypal-survey.com
+.paypal-survey.org
+.paypal-team.com
+.paypal-viewpoints.net
+.paypal.ca
+.paypal.com
+.paypal.com.cn
+.paypal.com.sg
+.paypal.info
+.paypal.jp
+.paypal.me
+.paypal.net.cn
+.paypal.org.cn
+.paypal.so
+.paypal.us
+.paypalbeacon.com
+.paypalbenefits.com
+.paypalbrasil.com
+.paypalcommunity.cn
+.paypalcommunity.com
+.paypalcommunity.net
+.paypalcommunity.org
+.paypalcorp.com
+.paypalcredit.com
+.paypalcreditcard.com
+.paypalgivingfund.org
+.paypalhere.cn
+.paypalhere.com
+.paypalhere.com.cn
+.paypalhere.info
+.paypalhere.net
+.paypalhere.org
+.paypalhere.tv
+.paypali.net
+.paypalinc.com
+.paypalindia.com
+.paypalinsuranceservices.org
+.paypall.com
+.paypallabs.com
+.paypalme.com
+.paypalnet.net
+.paypalnet.org
+.paypalnetwork.info
+.paypalnetwork.net
+.paypalnetwork.org
+.paypalobjects.com
+.paypalonline.net
+.paypalonline.org
+.paypalprepagata.com
+.paypalprepagata.net
+.paypalservice.com
+.paypalshopping.com
+.paypalshopping.net
```
……其余 44 条见 changes.json

</details>

<details>
<summary><code>clash-domain/Proxy.yaml</code></summary>

新增（11）：

```text
+.megafon.cloud
+.megapbx.ru
+.megatech-it.ru
+.mgts.ru
+.mobileid.ru
+.multifon.ru
+.o7.com
+.onlime.ru
+.rostelecom-rb.ru
+.spd-mgts.ru
+.xn--e1aapchhekkk.xn--p1ai
```

</details>

<details>
<summary><code>clash-ipcidr/China-ipcidr.yaml</code></summary>

新增（13）：

```text
2001:678:12b8::/48
2001:678:12c4::/48
2001:67c:2c1c::/48
2001:67c:ebc::/48
2001:df3:d0c0::/48
2001:df4:a1c0::/48
2001:df4:e140::/48
2001:df4:e142::/47
2001:df5:2fc0::/48
2001:df5:4cc0::/48
2001:df7:d940::/48
2402:8420::/32
2a0a:d682:e000::/36
```

</details>

<details>
<summary><code>clash-ipcidr/Google-ipcidr.yaml</code></summary>

新增（137）：

```text
136.36.64.0/21
136.36.72.0/22
136.36.76.0/23
136.36.78.0/26
136.36.78.128/25
136.36.78.64/28
136.36.78.80/30
136.36.78.85/32
136.36.78.86/31
136.36.78.88/29
136.36.78.96/27
136.36.79.0/24
136.47.10.0/23
136.47.8.0/26
136.47.8.128/25
136.47.8.64/29
136.47.8.72/31
136.47.8.74/32
136.47.8.76/30
136.47.8.80/28
136.47.8.96/27
136.47.9.0/24
136.51.30.0/25
136.60.64.0/25
136.60.64.128/26
136.60.64.192/29
136.60.64.200/30
136.60.64.204/31
136.60.64.207/32
136.60.64.208/28
136.60.64.224/27
136.60.65.0/24
136.60.66.0/23
192.166.140.0/22
2605:a601:8044::/46
2605:a601:806a:4000::/51
2605:a601:806a:6000::/53
2605:a601:806a:6800::/54
2605:a601:806a:6c00::/55
2605:a601:806a:6e01::/64
2605:a601:806a:6e02::/63
2605:a601:806a:6e04::/62
2605:a601:806a:6e08::/61
2605:a601:806a:6e10::/60
2605:a601:806a:6e20::/59
2605:a601:806a:6e40::/58
2605:a601:806a:6e80::/57
2605:a601:806a:6f00::/56
2605:a601:806a:7000::/52
2605:a601:806a::/50
2605:a601:81d8::/45
2605:a601:81f0::/45
2605:a601:9534::/47
2605:a601:9a00::/46
2605:a601:9a2c::/46
2605:a601:9c54:2000::/52
2605:a601:9c54:3000::/55
2605:a601:9c54:3201::/64
2605:a601:9c54:3202::/63
2605:a601:9c54:3204::/62
2605:a601:9c54:3208::/61
2605:a601:9c54:3210::/60
2605:a601:9c54:3220::/59
2605:a601:9c54:3240::/58
2605:a601:9c54:3280::/57
2605:a601:9c54:3300::/56
2605:a601:9c54:3400::/54
2605:a601:9c54:3800::/53
2605:a601:9c54:4000::/50
2605:a601:9c54::/51
2605:a601:a050::/44
2605:a601:a0a0::/43
2605:a601:a0e0::/47
2605:a601:a3c8::/48
2605:a601:a3c9:4000::/51
2605:a601:a3c9:6000::/52
2605:a601:a3c9:7000::/53
2605:a601:a3c9:7800::/54
2605:a601:a3c9:7c00::/55
2605:a601:a3c9:7e00::/56
2605:a601:a3c9:7f01::/64
2605:a601:a3c9:7f02::/63
2605:a601:a3c9:7f04::/62
2605:a601:a3c9:7f08::/61
2605:a601:a3c9:7f10::/60
2605:a601:a3c9:7f20::/59
2605:a601:a3c9:7f40::/58
2605:a601:a3c9:7f80::/57
2605:a601:a3c9:8000::/49
2605:a601:a3c9::/50
2605:a601:a3ca::/47
2605:a601:a3cc::/46
2605:a601:a3f0::/45
2605:a601:a540::/44
2605:a601:a55c:8000::/50
2605:a601:a55c::/49
2605:a601:a55c:c000::/51
2605:a601:a55c:e000::/52
2605:a601:a55c:f000::/54
2605:a601:a55c:f401::/64
2605:a601:a55c:f402::/63
2605:a601:a55c:f404::/62
2605:a601:a55c:f408::/61
2605:a601:a55c:f410::/60
2605:a601:a55c:f420::/59
2605:a601:a55c:f440::/58
2605:a601:a55c:f480::/57
2605:a601:a55c:f500::/56
2605:a601:a55c:f600::/55
2605:a601:a55c:f800::/53
2605:a601:a55d::/48
2605:a601:a724::/46
2605:a601:a730::/45
2605:a601:a984:8000::/50
2605:a601:a984::/49
2605:a601:a984:c000::/51
2605:a601:a984:e000::/54
2605:a601:a984:e400::/56
2605:a601:a984:e501::/64
2605:a601:a984:e502::/63
2605:a601:a984:e504::/62
2605:a601:a984:e508::/61
2605:a601:a984:e510::/60
2605:a601:a984:e520::/59
2605:a601:a984:e540::/58
2605:a601:a984:e580::/57
2605:a601:a984:e600::/55
2605:a601:a984:e800::/53
2605:a601:a984:f000::/52
2605:a601:a985::/48
2605:a601:a986::/47
2605:a601:a988::/45
2605:a601:a9c8:4000::/50
2605:a601:aa98::/45
2606:ec80:20::/44
2607:9180:2000::/40
2a04:7200::/29
```

删除（312）：

```text
136.36.64.0/20
136.47.8.0/22
136.51.30.0/26
136.51.30.64/29
136.51.30.72/30
136.51.30.76/31
136.51.30.78/32
136.51.30.80/28
136.51.30.96/27
136.60.64.0/22
2605:a601:8044::/47
2605:a601:8046:4000::/51
2605:a601:8046:6000::/54
2605:a601:8046:6400::/55
2605:a601:8046:6600::/56
2605:a601:8046:6701::/64
2605:a601:8046:6702::/63
2605:a601:8046:6704::/62
2605:a601:8046:6708::/61
2605:a601:8046:6710::/60
2605:a601:8046:6720::/59
2605:a601:8046:6740::/58
2605:a601:8046:6780::/57
2605:a601:8046:6800::/53
2605:a601:8046:7000::/52
2605:a601:8046:8000::/49
2605:a601:8046::/50
2605:a601:8047::/48
2605:a601:806a::/49
2605:a601:81d8::/47
2605:a601:81da:1000::/53
2605:a601:81da:1800::/54
2605:a601:81da:1c00::/55
2605:a601:81da:1e01::/64
2605:a601:81da:1e02::/63
2605:a601:81da:1e04::/62
2605:a601:81da:1e08::/61
2605:a601:81da:1e10::/60
2605:a601:81da:1e20::/59
2605:a601:81da:1e40::/58
2605:a601:81da:1e80::/57
2605:a601:81da:1f00::/56
2605:a601:81da:2000::/51
2605:a601:81da:4000::/50
2605:a601:81da:8000::/49
2605:a601:81da::/52
2605:a601:81db::/48
2605:a601:81dc::/46
2605:a601:81f0:8000::/50
2605:a601:81f0::/49
2605:a601:81f0:c000::/52
2605:a601:81f0:d000::/54
2605:a601:81f0:d400::/56
2605:a601:81f0:d501::/64
2605:a601:81f0:d502::/63
2605:a601:81f0:d504::/62
2605:a601:81f0:d508::/61
2605:a601:81f0:d510::/60
2605:a601:81f0:d520::/59
2605:a601:81f0:d540::/58
2605:a601:81f0:d580::/57
2605:a601:81f0:d600::/55
2605:a601:81f0:d800::/53
2605:a601:81f0:e000::/51
2605:a601:81f1::/48
2605:a601:81f2::/47
2605:a601:81f4::/46
2605:a601:9534:8000::/51
2605:a601:9534::/49
2605:a601:9534:a000::/53
2605:a601:9534:a800::/54
2605:a601:9534:ac00::/56
2605:a601:9534:ad01::/64
2605:a601:9534:ad02::/63
2605:a601:9534:ad04::/62
2605:a601:9534:ad08::/61
2605:a601:9534:ad10::/60
2605:a601:9534:ad20::/59
2605:a601:9534:ad40::/58
2605:a601:9534:ad80::/57
2605:a601:9534:ae00::/55
2605:a601:9534:b000::/52
2605:a601:9534:c000::/50
2605:a601:9535::/48
2605:a601:9a00::/47
2605:a601:9a02::/48
2605:a601:9a03:2000::/52
2605:a601:9a03:3000::/54
2605:a601:9a03:3400::/55
2605:a601:9a03:3600::/56
2605:a601:9a03:3701::/64
2605:a601:9a03:3702::/63
2605:a601:9a03:3704::/62
2605:a601:9a03:3708::/61
2605:a601:9a03:3710::/60
2605:a601:9a03:3720::/59
2605:a601:9a03:3740::/58
2605:a601:9a03:3780::/57
2605:a601:9a03:3800::/53
2605:a601:9a03:4000::/50
2605:a601:9a03:8000::/49
2605:a601:9a03::/51
2605:a601:9a2c::/47
2605:a601:9a2e::/48
2605:a601:9a2f:4000::/51
2605:a601:9a2f:6000::/52
2605:a601:9a2f:7000::/54
2605:a601:9a2f:7401::/64
2605:a601:9a2f:7402::/63
2605:a601:9a2f:7404::/62
2605:a601:9a2f:7408::/61
2605:a601:9a2f:7410::/60
2605:a601:9a2f:7420::/59
2605:a601:9a2f:7440::/58
2605:a601:9a2f:7480::/57
2605:a601:9a2f:7500::/56
2605:a601:9a2f:7600::/55
2605:a601:9a2f:7800::/53
2605:a601:9a2f:8000::/49
2605:a601:9a2f::/50
2605:a601:9c54::/49
2605:a601:a050::/45
2605:a601:a058::/46
2605:a601:a05c::/47
2605:a601:a05e::/48
2605:a601:a05f:4000::/52
2605:a601:a05f:5000::/55
2605:a601:a05f:5200::/56
2605:a601:a05f:5301::/64
2605:a601:a05f:5302::/63
2605:a601:a05f:5304::/62
2605:a601:a05f:5308::/61
2605:a601:a05f:5310::/60
2605:a601:a05f:5320::/59
2605:a601:a05f:5340::/58
2605:a601:a05f:5380::/57
2605:a601:a05f:5400::/54
2605:a601:a05f:5800::/53
2605:a601:a05f:6000::/51
2605:a601:a05f:8000::/49
2605:a601:a05f::/50
2605:a601:a0a0::/44
2605:a601:a0b0::/47
2605:a601:a0b2::/48
2605:a601:a0b3:8000::/50
2605:a601:a0b3::/49
2605:a601:a0b3:c000::/52
2605:a601:a0b3:d000::/54
2605:a601:a0b3:d401::/64
2605:a601:a0b3:d402::/63
2605:a601:a0b3:d404::/62
2605:a601:a0b3:d408::/61
2605:a601:a0b3:d410::/60
2605:a601:a0b3:d420::/59
2605:a601:a0b3:d440::/58
2605:a601:a0b3:d480::/57
2605:a601:a0b3:d500::/56
2605:a601:a0b3:d600::/55
2605:a601:a0b3:d800::/53
2605:a601:a0b3:e000::/51
2605:a601:a0b4::/46
2605:a601:a0b8::/45
2605:a601:a0e0:8000::/51
2605:a601:a0e0::/49
2605:a601:a0e0:a000::/52
2605:a601:a0e0:b000::/53
2605:a601:a0e0:b800::/54
2605:a601:a0e0:bc00::/55
2605:a601:a0e0:be00::/56
2605:a601:a0e0:bf01::/64
2605:a601:a0e0:bf02::/63
2605:a601:a0e0:bf04::/62
2605:a601:a0e0:bf08::/61
2605:a601:a0e0:bf10::/60
2605:a601:a0e0:bf20::/59
2605:a601:a0e0:bf40::/58
2605:a601:a0e0:bf80::/57
2605:a601:a0e0:c000::/50
2605:a601:a0e1::/48
2605:a601:a3c8::/45
2605:a601:a3f0::/46
2605:a601:a3f4::/47
2605:a601:a3f6::/48
2605:a601:a3f7:8000::/53
2605:a601:a3f7:8800::/54
2605:a601:a3f7:8c00::/56
2605:a601:a3f7:8d01::/64
2605:a601:a3f7:8d02::/63
2605:a601:a3f7:8d04::/62
2605:a601:a3f7:8d08::/61
2605:a601:a3f7:8d10::/60
2605:a601:a3f7:8d20::/59
2605:a601:a3f7:8d40::/58
2605:a601:a3f7:8d80::/57
2605:a601:a3f7:8e00::/55
2605:a601:a3f7:9000::/52
2605:a601:a3f7::/49
2605:a601:a3f7:a000::/51
2605:a601:a3f7:c000::/50
2605:a601:a540:8000::/50
```
……其余 112 条见 changes.json

</details>

<details>
<summary><code>clash-ipcidr/Singapore-ipcidr.yaml</code></summary>

新增（2）：

```text
2a03:2887:ff05::/48
2a03:2887:ff06::/47
```

删除（2）：

```text
2a03:2887:ff04::/46
2a03:2887:ff30::/48
```

</details>

## 优化统计

| 规则组 | 输入 | 输出 | 重复 | 被覆盖 | 合并 |
| --- | --- | --- | --- | --- | --- |
| Direct | 3778 | 2566 | 347 | 22 | 859 |
| NS | 9 | 8 | 1 | 0 | 0 |
| AI | 853 | 339 | 468 | 22 | 39 |
| TikTok | 75 | 61 | 12 | 2 | 0 |
| Bilibili | 1539 | 1177 | 310 | 48 | 8 |
| Tencent | 3376 | 2650 | 558 | 167 | 0 |
| Netflix | 1303 | 1158 | 24 | 0 | 122 |
| YouTube | 361 | 184 | 176 | 1 | 0 |
| Google | 8695 | 7806 | 612 | 217 | 85 |
| Telegram | 97 | 54 | 33 | 0 | 10 |
| Japan | 547 | 308 | 195 | 43 | 0 |
| HK | 4618 | 3784 | 540 | 42 | 286 |
| Apple | 3468 | 1594 | 1428 | 285 | 4 |
| Singapore | 2202 | 1092 | 1100 | 5 | 6 |
| America | 3010 | 1939 | 877 | 187 | 10 |
| ChinaMedia | 9985 | 7256 | 2223 | 426 | 117 |
| OneDrive | 1086 | 684 | 385 | 13 | 8 |
| Microsoft | 1511 | 770 | 611 | 123 | 14 |
| Media | 13903 | 12602 | 1002 | 262 | 55 |
| Proxy | 69509 | 30071 | 32796 | 6540 | 102 |
| China | 506931 | 123435 | 337589 | 72 | 45836 |

## 会触发 DNS 解析的手写内联规则

按原样保留（未加 no-resolve）：
- `GEOIP,CN: DIRECT`
