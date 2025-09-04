# scroll_controller.py

# collections 是 Python 内置的集合模块，提供了额外的数据结构
# 这里主要使用其中的 deque（双端队列）来实现滚动方向的堆栈管理
import collections

class ScrollController:
    """
    管理平滑滚动的状态和物理计算。
    这个类的核心是 update(delta) 方法，它被一个高频循环调用。
    """
    def __init__(self, config, platform_scroller):
        """
        初始化滚动控制器。
        
        Args:
            config (AppConfig): 应用程序的配置对象，用于获取滚动参数。
            platform_scroller (WinPlatformScroller): 平台特定的滚动实现对象。
        """
        # --- 依赖注入 ---
        self.config = config
        self.platform_scroller = platform_scroller
        
        # --- 状态变量 ---
        # 使用双端队列(deque)作为栈，来跟踪当前生效的滚动方向。
        # 当用户按下'向上'键，一个'up'标志被推入，释放时弹出。
        # 这样做可以正确处理用户同时按下'向上'和'向下'键的情况。
        self.y_wheel_stack = collections.deque()
        
        # --- 物理计算变量 ---
        # `wheel_duration`: 浮点数，持续按住滚动键的时间（秒）。
        # 按住时间越长，此值越大，导致滚动速度越快。
        self.wheel_duration = 0.0
        
        # `scroll_accumulator`: 浮点数，用于累积计算出的、带有小数的滚动距离。
        # 因为我们每次只能滚动整数个像素，这个累加器可以防止丢失小数部分的精度，
        # 使得长期滚动更加平滑。
        self.scroll_accumulator = 0.0

    def is_wheeling(self) -> bool:
        """
        检查当前是否处于任何滚动状态。
        
        Returns:
            bool: 如果y_wheel_stack不为空，则为True，表示正在滚动。
        """
        return bool(self.y_wheel_stack)

    def _calculate_velocity(self) -> float:
        """
        根据按住滚动键的持续时间，动态计算当前的滚动速度。
        
        公式: 当前速度 = min(最大速度, 初始速度 + 加速度 * 持续时间)
        
        Returns:
            float: 计算出的当前滚动速度（像素/秒）。
        """
        # 从配置中获取物理参数
        initial_v = self.config.SCROLL_INITIAL_VELOCITY
        max_v = self.config.SCROLL_MAX_VELOCITY
        accel = self.config.SCROLL_ACCELERATION
        
        # 应用公式
        velocity = initial_v + accel * self.wheel_duration
        
        # 确保速度不超过最大值
        return min(max_v, velocity)

    def update(self, delta: float):
        """
        主更新方法，由外部循环（如mouse_movement_worker）在高频调用。
        
        Args:
            delta (float): 距离上次调用的时间间隔（秒）。
        """
        # 如果当前没有滚动，重置持续时间并退出
        if not self.is_wheeling():
            self.wheel_duration = 0.0
            self.scroll_accumulator = 0.0
            return
        
        # 累积按住滚动键的时间
        self.wheel_duration += delta
        
        # 计算当前帧的速度
        velocity = self._calculate_velocity()
        
        # 计算当前帧理论上应该滚动的距离（带小数）
        # 距离 = 速度 * 时间
        distance = velocity * delta
        
        # 根据栈顶的方向决定滚动的正负
        # 栈顶元素 'down' 表示向下滚动，对应负距离
        direction = -1 if self.y_wheel_stack[-1] == 'down' else 1
        
        # 累积滚动距离
        self.scroll_accumulator += distance * direction
        
        # 取出累加器中的整数部分作为本次实际要滚动的像素值
        pixels_to_scroll = int(self.scroll_accumulator)
        
        # 从累加器中减去已滚动的整数部分，保留小数部分以供下次计算
        self.scroll_accumulator -= pixels_to_scroll
        
        # 如果有实际需要滚动的像素，则调用平台实现
        if pixels_to_scroll != 0:
            self.platform_scroller.scroll_vertical(pixels_to_scroll)

    def start_scroll_down(self):
        """注册开始向下滚动的意图。"""
        # 为避免重复添加，先检查 'down' 是否已在栈中
        if 'down' not in self.y_wheel_stack:
            self.y_wheel_stack.append('down')

    def stop_scroll_down(self):
        """注册停止向下滚动的意图。"""
        try:
            # 安全地从栈中移除 'down'
            self.y_wheel_stack.remove('down')
        except ValueError:
            # 如果 'down' 不在栈中（例如，异常退出时），则忽略错误
            pass

    def start_scroll_up(self):
        """注册开始向上滚动的意图。"""
        if 'up' not in self.y_wheel_stack:
            self.y_wheel_stack.append('up')

    def stop_scroll_up(self):
        """注册停止向上滚动的意图。"""
        try:
            self.y_wheel_stack.remove('up')
        except ValueError:
            pass