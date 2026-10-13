# 测量 recipes (browser_exec / CDP)

> 目的:**先拿到数字,再谈优化。** 每段都是可直接改用的片段。

## 1. FPS + 状态(按 route)

```python
js("""(() => { location.hash='#/<route>'; return true; })()""")
time.sleep(3)
print(js("""(() => {
  const t = document.body.innerText.replace(/\\s+/g, ' ');
  const s = t.match(/Status:[^F]{0,24}/);
  const f = t.match(/FPS: *[0-9.]+/);
  return (s ? s[0] : '?') + ' | ' + (f ? f[0] : '?');
})()"""))
```

跑遍全部 route + 全部后端 tab(2D / GL / GPU)。全 60 = vsync 顶满 = 无 headroom 信号。

## 2. 帧间隔 + long task(判断主线程是否被堵)

```python
print(js("""new Promise(res => {
  const iv = []; let n = 0; let last = performance.now();
  const po = new PerformanceObserver(l => { window.__long = l.getEntries().length; });
  try { po.observe({entryTypes: ['longtask']}); } catch (e) {}
  function f(t) { iv.push(t - last); last = t; if (++n < 180) requestAnimationFrame(f); else {
    iv.sort((a,b)=>a-b);
    po.disconnect();
    res({median:+iv[iv.length>>1].toFixed(1),
         p95:+iv[(iv.length*0.95)|0].toFixed(1),
         max:+iv[iv.length-1].toFixed(1), longTasks: window.__long||0});
  }}
  requestAnimationFrame(f);
})"""))
```

中位 ≈16.7ms 且 longTasks 0 = 有余量。longTasks > 0 才是真的 CPU 瓶颈。

## 3. 每帧 JS 边界穿越

**必须在下一次 render 之前装 spy**,否则引擎已缓存 `Function` 对象,补丁被绕过、计数恒 0
(看起来像「loop 没跑」):

```python
js("""(() => {
  window.__rc = 0;
  const g = Reflect.get, s = Reflect.set;
  Reflect.get = function(...a){ window.__rc++; return g.apply(this, a); };
  Reflect.set  = function(...a){ window.__rc++; return s.apply(this, a); };
  return 'installed';
})()""")
time.sleep(6)
n = js("window.__rc")
frames = fps * 6
print(f"{n} crossings / {frames:.0f} frames = {n/frames:.1f} per frame")
```

## 4. 每次 signal 更新的真实开销(框架 patch 是否细粒度)

```python
js("""(() => {
  window.__w = {attr:0};
  const sa = Element.prototype.setAttribute;
  Element.prototype.setAttribute = function(k,v){ window.__w.attr++; return sa.call(this,k,v); };
  return 'installed';
})()""")
# 触发一次真实更新,**并先确认值真的变了**
print(js("""(() => { const b=[...document.querySelectorAll('button')]
  .find(x=>/add|increment|\\+/i.test(x.innerText)); if(b) b.click(); return !!b; })()"""))
time.sleep(0.5)
print("attr writes:", js("window.__w.attr"))
```

`attr writes: 0` + crossings ≈1 = 细粒度 patch 生效,框架没有退化。
**但必须先验证点击真的生效**(值变化),否则会得到一个自信但无意义的 0。

## 5. GPU canvas 像素

WebGL 在 `requestAnimationFrame` 内**立即** `readPixels`(合成后读必为 0,因为
`preserveDrawingBuffer` 默认 false)。WebGPU `drawImage` 恒黑,需引擎 readback API
或 scrollIntoView + 截图。详见 `euv-engine-renderer-api` 的 silent-failure reference。

## 判读

| 观测 | 结论 |
|---|---|
| 全 route 60 FPS + 0 long task | 无 headroom,应明确说「没什么可做的」 |
| 单页 <60 | 先区分 demo 负载 vs 引擎开销 |
| crossings/frame 很低 | 缓存已生效,进一步压收益趋零 |
| attr writes 0 | 框架 patch 已细粒度 |
