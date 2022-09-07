# alert bot

统计指定的 rum groups 的每日新增 block 数，trx 数，每个 pubkey 的新增 trxs 数，并把统计结果通过 mixin bot 发送给指定人员（比如开发者，运营维护人员）。

### 如何部署？

1、运行 rum fullnode，且已加入相关 groups

2、拷贝代码，安装 python 及相关依赖

```sh
pip install -r requriments.txt
```

- Mixin [mixinsdk](https://pypi.org/project/mixinsdk/)
- QuoRum [rumpy](https://github.com/liujuanjuan1984/rumpy)
- [officy](https://github.com/liujuanjuan1984/officy)

3、参考 config_sample.py 创建 config.py 并修改配置

其中 mixin keystore 通过 mixin dashboard 后台申请获得

4、执行脚本；或设定定时任务，按所需频率执行脚本

一次性执行如下；注：首次执行时，如果种子网络数据量较大，会需要一些时间。

```sh
python do_it.py
```

windows 操作系统可以通过 `任务计划程序` 来设定每天 7、19 点各执行一次脚本。