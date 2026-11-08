// kernel-adapter：用固定版本 Mihomo 的真实配置解析、rule-provider 读取与规则求值，
// 对一组请求元数据给出「首个命中的规则与目标」。只暴露测试所需接口，不复制任何规则算法。
//
// 用法：kernel-adapter <home 目录> <config.yaml> <queries.jsonl>
// 输出（stdout，JSON Lines）：先输出每个 provider 的加载条目数，再输出每个请求的结果。
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"net/netip"
	"os"
	"sort"
	"time"

	"github.com/metacubex/mihomo/config"
	C "github.com/metacubex/mihomo/constant"
	_ "github.com/metacubex/mihomo/hub/executor" // config 通过 go:linkname 引用其中的函数
	"github.com/metacubex/mihomo/log"
)

type query struct {
	ID      string `json:"id"`
	Host    string `json:"host"`
	IP      string `json:"ip"`
	Network string `json:"network"`
	Port    uint16 `json:"port"`
}

type result struct {
	Kind      string `json:"kind"`
	ID        string `json:"id,omitempty"`
	Index     int    `json:"index"`
	Rule      string `json:"rule,omitempty"`
	Adapter   string `json:"adapter,omitempty"`
	Resolve   bool   `json:"resolve_requested,omitempty"`
	ResolveBy string `json:"resolve_by,omitempty"`
	Provider  string `json:"provider,omitempty"`
	Count     int    `json:"count,omitempty"`
	Nanos     int64  `json:"nanos,omitempty"`
}

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", args...)
	os.Exit(2)
}

func main() {
	if len(os.Args) != 4 {
		fail("usage: kernel-adapter <home> <config.yaml> <queries.jsonl>")
	}
	log.SetLevel(log.SILENT)
	C.SetHomeDir(os.Args[1])
	buf, err := os.ReadFile(os.Args[2])
	if err != nil {
		fail("read config: %v", err)
	}
	cfg, err := config.Parse(buf)
	if err != nil {
		fail("parse config: %v", err)
	}
	writer := bufio.NewWriterSize(os.Stdout, 1<<20)
	out := json.NewEncoder(writer)
	defer writer.Flush()

	names := make([]string, 0, len(cfg.RuleProviders))
	for name := range cfg.RuleProviders {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		provider := cfg.RuleProviders[name]
		started := time.Now()
		if err := provider.Initial(); err != nil {
			fail("load provider %s: %v", name, err)
		}
		elapsed := time.Since(started).Nanoseconds()
		_ = out.Encode(result{Kind: "provider", Provider: name, Count: provider.Count(), Nanos: elapsed})
	}

	file, err := os.Open(os.Args[3])
	if err != nil {
		fail("open queries: %v", err)
	}
	defer file.Close()
	// Windows 上单次计时粒度过粗，只累计整批匹配耗时，输出平均值
	var matchTotal time.Duration
	queries := 0
	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, 1<<20), 1<<20)
	for scanner.Scan() {
		var q query
		if err := json.Unmarshal(scanner.Bytes(), &q); err != nil {
			fail("bad query: %v", err)
		}
		metadata := &C.Metadata{Host: q.Host, DstPort: q.Port, NetWork: C.TCP}
		if q.Network == "udp" {
			metadata.NetWork = C.UDP
		}
		if q.IP != "" {
			addr, err := netip.ParseAddr(q.IP)
			if err != nil {
				fail("bad ip %q: %v", q.IP, err)
			}
			metadata.DstIP = addr
		}
		resolve := false
		resolveBy := ""
		current := ""
		helper := C.RuleMatchHelper{
			// 记录第一条请求解析的规则：DNS 是否被触发、由谁触发，是 no-resolve 验收的依据
			ResolveIP: func() {
				if !resolve {
					resolve = true
					resolveBy = current
				}
			},
			FindProcess: func() {},
		}
		res := result{Kind: "query", ID: q.ID, Index: -1}
		started := time.Now()
		for index, rule := range cfg.Rules {
			current = rule.RuleType().String() + "," + rule.Payload()
			if matched, adapter := rule.Match(metadata, helper); matched {
				res.Index = index
				res.Rule = rule.RuleType().String() + "," + rule.Payload()
				res.Adapter = adapter
				break
			}
		}
		matchTotal += time.Since(started)
		queries++
		res.Resolve = resolve
		res.ResolveBy = resolveBy
		_ = out.Encode(res)
	}
	if err := scanner.Err(); err != nil {
		fail("read queries: %v", err)
	}
	_ = out.Encode(result{Kind: "summary", Count: queries, Nanos: matchTotal.Nanoseconds()})
}
