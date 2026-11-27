# Builds the small pictures used by «دليل القارئ» (the reader's guide).
# Run with the site served locally:  python3 -m http.server 8765  (in the repo)
#   python3 tools/guide_shots.py OUTDIR
# Each picture is a crop of the real app (light mode, portrait), so the guide
# always shows exactly what the reader sees on the screen.
import sys, json
from playwright.sync_api import sync_playwright
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/shots'
URL = 'http://localhost:8765/index.html'

def run():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = b.new_page(viewport={'width': 400, 'height': 1300}, device_scale_factor=2)
        pg.goto(URL); pg.wait_for_timeout(4500)
        ev = lambda js: pg.evaluate(js)
        def shot(key, sel, pad=3, idx=0):
            els = pg.query_selector_all(sel)
            if len(els) <= idx: print('MISSING', key, sel); return
            el = els[idx]
            try: el.scroll_into_view_if_needed(timeout=1500)
            except Exception: pass
            bb = el.bounding_box()
            if not bb or bb['width'] < 1: print('HIDDEN', key, sel); return
            clip = {'x': max(0, bb['x'] - pad), 'y': max(0, bb['y'] - pad), 'width': bb['width'] + 2 * pad, 'height': bb['height'] + 2 * pad}
            pg.screenshot(path=f'{OUT}/{key}.png', clip=clip)
        def area(key, x, y, w, h):
            pg.screenshot(path=f'{OUT}/{key}.png', clip={'x': x, 'y': y, 'width': w, 'height': h})
        pg.add_style_tag(content='#toast{display:none !important}')
        def top(key, sel, idx=0, maxh=320, pad=0):
            els = pg.query_selector_all(sel)
            if len(els) <= idx: print('MISSING', key, sel); return
            el = els[idx]
            bb = el.bounding_box()
            pg.screenshot(path=f'{OUT}/{key}.png', clip={'x': bb['x'] - pad, 'y': bb['y'] - pad, 'width': bb['width'] + 2 * pad, 'height': min(bb['height'], maxh) + 2 * pad})
        # hide the install banner if any
        ev("document.querySelectorAll('.install-banner,#installBanner').forEach(e=>e.remove())")
        # ---- sidebar (as the app opens) ----
        ev("switchMushaf('aam')"); pg.wait_for_timeout(600)
        ev("openSidebar('surah', true)"); pg.wait_for_timeout(800)
        shot('sb_header', '.sidebar-colheader', 0)
        shot('sb_aam', '#resumeBox', 2)
        shot('sb_khatma', '#resumeBoxKhatma', 2)
        top('sb_surah_list', '#sidebarBody', 0, 260)
        tabs = ['duas','surah','juz','page','bookmarks','recitation','voice','font','pagebg','fadl','stats','tajweed','guide','hijri','share']
        for t in tabs:
            shot('tab_' + t, f'.tab[data-tab={t}]', 0)
        ev("closeSidebar()"); pg.wait_for_timeout(700)
        # ---- header ----
        shot('hdr', 'header', 0)
        shot('menu', '#menuBtn', 2)
        shot('moon', '#darkModeBtn', 2)
        shot('date', '#headerClockDate', 2)
        shot('search', '#headerSearch', 2)
        # ---- gold bar ----
        ev("centerOn(1)"); pg.wait_for_timeout(900)
        shot('gold', '#floatingFrameBar', 0)
        shot('g_bookmark', '#floatingFrameBar .fbBookmarkSlot', 2)
        shot('g_fromto', '#floatingFrameBar .fbFromTo', 2)
        shot('g_juz', '#floatingFrameBar .fbJuz', 3)
        shot('g_name', '#floatingFrameBar .fbNameZone', 3)
        shot('g_icon', '#floatingFrameBar .surah-place-icon', 2)
        shot('g_nums', '#floatingFrameBar .fbNums', 3)
        shot('g_hizb', '#floatingFrameBar .fbHizb', 3)
        shot('g_rub', '#floatingFrameBar .fbRub', 3)
        shot('g_circle', '#floatingFrameBar .fbCircleSlot', 2)
        ev("centerOn(2)"); pg.wait_for_timeout(900)
        for key, cls in (('g_juz', 'fbJuz'), ('g_hizb', 'fbHizb')):
            r = pg.evaluate(f"(()=>{{const e=document.querySelector('#floatingFrameBar .{cls}');const a=e.querySelector('.fbNavArrow');const b1=e.getBoundingClientRect(),b2=a?a.getBoundingClientRect():b1;const x=Math.min(b1.left,b2.left)-3,y=Math.min(b1.top,b2.top)-3;return [x,y,Math.max(b1.right,b2.right)-x+3,Math.max(b1.bottom,b2.bottom)-y+3]}})()")
            area(key, r[0], r[1], r[2], r[3])
        shot('g_icon_madani', '#floatingFrameBar .surah-place-icon', 2)
        ev("switchMushaf('khatma')"); pg.wait_for_timeout(1200)
        ev("closeSidebar()"); pg.wait_for_timeout(500)
        shot('g_icon_kh', '#floatingFrameBar .surah-place-icon', 2)
        shot('g_nums_kh', '#floatingFrameBar .fbNums', 3)
        ev("switchMushaf('aam')"); pg.wait_for_timeout(1200)
        ev("closeSidebar()"); pg.wait_for_timeout(500)
        ev("setWbwOn(true, true)"); pg.wait_for_timeout(500)
        shot('g_circle_on', '#floatingFrameBar .fbCircleSlot', 4)
        ev("setWbwOn(false, true)"); pg.wait_for_timeout(300)
        # surah listening bar (name frame turns red)
        ev("centerOn(1)"); pg.wait_for_timeout(700)
        ev("openSurahReciteBar(1)"); pg.wait_for_timeout(800)
        shot('g_name_on', '#floatingFrameBar .fbNameZone', 3)
        shot('bar_surah', '#reciteModeBar', 0)
        ev("document.getElementById('speedUpBtn').click(); document.getElementById('freeSpeedUpBtn').click()"); pg.wait_for_timeout(200)
        shot('fab_scroll_recite', '#freeAutoFab .fab-frame-scroll', 2)
        ev("document.getElementById('speedDownBtn').click(); document.getElementById('freeSpeedDownBtn').click()")
        ev("closeReciteModeBar()"); pg.wait_for_timeout(500)
        # ---- bottom bar (free layout) ----
        shot('fab_free', '#freeAutoFab', 0)
        shot('fab_rotate', '#rotateFrameFree', 2)
        shot('fab_scroll', '#freeAutoFab .fab-frame-scroll', 2)
        shot('fab_mic', '#micFrame', 2)
        shot('fab_stop', '#segStopFrame', 2)
        shot('fab_size', '#freeAutoFab .fab-frame-size', 2)
        shot('fab_back', '#backFrameFree', 2)
        ev("setSegStop(false)"); pg.wait_for_timeout(300)
        shot('fab_stop_off', '#segStopFrame', 2)
        ev("setSegStop(true)"); pg.wait_for_timeout(300)
        ev("startFreeAutoScroll()"); pg.wait_for_timeout(300)
        shot('fab_scroll_on', '#freeAutoFab .fab-frame-scroll', 2)
        ev("pauseFreeAutoScroll()"); pg.wait_for_timeout(300)
        # ---- text page ----
        ev("centerOn(2)"); pg.wait_for_timeout(1200)
        shot('t_surahbar', '.qh-grid', 4)
        shot('t_green', '.freePageTextBlock .gharib', 4, 3)
        shot('t_ayahnum', '.freePageTextBlock .ayahnum', 3, 4)
        ev("showGharib(document.querySelectorAll('.freePageTextBlock .gharib')[3])"); pg.wait_for_timeout(500)
        gp = pg.evaluate("(()=>{const w=document.querySelectorAll('.freePageTextBlock .gharib')[3].getBoundingClientRect();const q=ghPopup().getBoundingClientRect();const x=Math.min(w.left,q.left)-6,y=Math.min(w.top,q.top)-6;return [x,y,Math.max(w.right,q.right)-x+6,Math.max(w.bottom,q.bottom)-y+6]})()")
        area('t_meaning', max(0, gp[0]), max(0, gp[1]), min(400 - max(0, gp[0]), gp[2]), gp[3])
        ev("hideGharib()"); pg.wait_for_timeout(300)
        # 50th / 100th ayah of the mushaf (al-Baqara 43 and 93)
        ev("centerOn(7)"); pg.wait_for_timeout(1200)
        shot('t_50', '.freePageTextBlock .ayahnum-50:not(.ayahnum-100)', 4)
        ev("centerOn(15)"); pg.wait_for_timeout(1200)
        shot('t_100', '.freePageTextBlock .ayahnum-100', 4)
        shot('t_side', '.page-frame .pageSideLine', 0)
        ev("showAyahPopup(2, 255)"); pg.wait_for_timeout(900)
        shot('t_popup', '#ayahPopupCard', 0)
        ev("document.querySelector('#ayahPopup [data-action=recite]').click()"); pg.wait_for_timeout(900)
        ev("reciteAudio.pause && reciteAudio.pause()")
        shot('bar_ayah', '#reciteModeBar', 0)
        ev("closeReciteModeBar()"); pg.wait_for_timeout(400)
        ev("history.length"); 
        ev("document.getElementById('ayahPopup').style.display='none'")
        ev("showSegPanel('end', {s: 3, j: null, natural: true}, null, segWrap(), 0)"); pg.wait_for_timeout(600)
        shot('t_seg', '#segPanel', 3)
        ev("segPanelEl.style.display='none'; segEngaged=null")
        ev("openBookReader('tafsir', 1, 1)"); pg.wait_for_timeout(2000)
        top('t_book', '#bookReader', 0, 330)
        ev("document.getElementById('bookReader').style.display='none'")
        ev("showSearchPage('الصلاة')"); pg.wait_for_timeout(1500)
        hb = pg.evaluate("document.querySelector('header').getBoundingClientRect().bottom")
        area('t_search', 0, hb, 400, 300)
        ev("hideSearchPage()"); pg.wait_for_timeout(300)
        # ---- sidebar tabs' contents ----
        def tab(t):
            ev(f"openSidebar('{t}')"); pg.wait_for_timeout(700)
        tab('duas'); top('c_duas', '#sidebarBody', 0, 240)
        tab('juz'); top('c_juz', '#sidebarBody', 0, 200)
        tab('page'); top('c_page', '#sidebarBody', 0, 160)
        tab('recitation'); top('c_reciter', '#sidebarBody .sb-sub-current', 0, 200)
        top('c_selected', '#sidebarBody .sb-custom-recite', 0, 330)
        tab('voice'); top('c_voice', '#sidebarBody .voice-start-btn', 0, 100, 4)
        tab('font')
        for i in range(4): top(f'c_font{i+1}', '#sidebarBody .fo-card', i, 400)
        ev("(()=>{const sb=document.getElementById('sidebarBody');const c=sb.querySelectorAll('.fo-card')[4];sb.scrollTop=c.offsetTop-sb.offsetTop-4;})()"); pg.wait_for_timeout(400)
        top('c_font5', '#sidebarBody .fo-card', 4, 300)
        tab('pagebg'); top('c_pagebg', '#sidebarBody', 0, 230)
        tab('hijri'); top('c_hijri', '#sidebarBody', 0, 270)
        tab('share'); top('c_share', '#sidebarBody', 0, 300)
        tab('stats'); top('c_stats', '#sidebarBody', 0, 260)
        tab('tajweed'); top('c_tajweed', '#sidebarBody', 0, 260)
        tab('fadl'); top('c_fadl', '#sidebarBody', 0, 260)
        ev("closeSidebar()"); pg.wait_for_timeout(500)
        # dark mode button (sun)
        ev("document.getElementById('darkModeBtn').click()"); pg.wait_for_timeout(1500)
        shot('sun', '#darkModeBtn', 2)
        ev("document.getElementById('darkModeBtn').click()"); pg.wait_for_timeout(300)
        # standard (page) layout bottom bar
        ev("applyLayoutMode('bound')"); pg.wait_for_timeout(3000)
        shot('fab_bound', '#autoFab', 0)
        ev("applyLayoutMode('free')"); pg.wait_for_timeout(800)
        b.close()

run()
