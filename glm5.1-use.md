
蓝区使用opencode glm 5.1
xutao164<xutao164@huawei.com>
我<2423750782@qq.com>
【计算装备团队发放AI账号通知】
安全使用承诺书已发放至W3待办，试用前请先签署
姓名：许涛
工号：x00922209
蓝区百炼模型GLM5
wiki配置指导文档：https://wiki.huawei.com/domains/164642/wiki/339081/WIKI2026033010604221
对应API KEY ：sk-e6983a31d5c64ddebdac10fdf514e162
支撑人员 李娜 l30074365

阿里-百炼

2026-03-30 17:23 由 曹硕 00583846 创建，于 2026-05-09 15:25 由 曹硕 00583846 最后修改。 

内容存疑 点我

按照统一的要求，使用OpenCode；目前提供的百炼大模型有试点GLM 5(在模型列表中选择glm-5)、内测Qwen3.6(在模型列表中选择Qwen3.6 Plus)，其他模型暂不支持

OpenCode接入百炼推理服务：

https://help.aliyun.com/zh/model-studio/opencode?spm=a2c4g.11186623.help-menu-2400256.d_0_4_8.4f932842pOjIbQ

官方文档给的示例是Qwen的，如果是GLM5的，也可以查看公司内部由产业自行编写的指导：

https://wiki.huawei.com/domains/165083/wiki/340256/WIKI2026033010604457


 

厂商成立了官方的支撑群组，有问题可以加群反馈，内有厂商技术支撑人员值班

蓝区百炼-OpenCode(GLM5)配置

2026-03-30 17:31 由 万世军 00884242 创建，于 2026-04-20 21:07 由 万世军 00884242 最后修改。 

内容存疑 点我

本文介绍如何在 OpenCode 中配置和对接百炼的GLM 5模型。
前提条件：已申请使用权限获得API_KEY并有蓝区环境。

1. 安装 OpenCode
1. 安装nodejs
按照下图安装测试

安装nodejs的同时会安装npm

2. 安装OpenCode
命令行里执行以下命令安装 OpenCode

1
npm install -g opencode-ai
​
安装结束后，执行以下命令，若显示版本号则安装成功。

1
opencode --version
​


3. 使用
启动OpenCode
注意 在开源空间场中，请务必在vs-code的Terminal中运行OpenCode，如果直接在系统的cmd或Power shell中运行会卡死
1
opencode
​
对接API
输入 /connect


选择 Alibaba(China)


输入key


选择GLM-5


选择模型
输入 /models

选择GLM-5 Alibaba (China)


4. 其他问题
1、开源空间连不上网络


1
2
蓝区生态空间找到一篇这个参考里面配置：
https://wiki.huawei.com/domains/3979/wiki/10048/WIKI2026020910113990
​
5.下载openCode安装包：
在openCode社区官网下载对应版本，连接如下：
https://opencode.ai/download



 

 