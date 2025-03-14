/**
 * 迷雾效果模块
 * 处理游戏中的迷雾和云雾效果
 * 所有样式都限定在#game-map-container选择器内，确保只影响地图区域
 */

// 迷雾效果配置
const FogConfig = {
    // 设置为true启用云雾效果，设置为false使用旧的迷雾效果
    useCloudFogEffect: true,
    // 云朵数量
    cloudCount: 25,
    // 云朵最小尺寸
    minCloudSize: 60,
    // 云朵动画最短持续时间(秒)
    minAnimationDuration: 8,
    // 云朵动画最长持续时间(秒)
    maxAnimationDuration: 20
};

/**
 * 创建云朵效果
 * @param {HTMLElement} container - 云朵容器元素
 */
function createClouds(container) {
    // 清空容器
    container.innerHTML = '';
    
    // 获取容器尺寸
    const containerWidth = container.offsetWidth || 300;
    const containerHeight = container.offsetHeight || 200;
    
    // 创建多个云朵元素
    for (let i = 0; i < FogConfig.cloudCount; i++) {
        const cloud = document.createElement('div');
        cloud.className = 'cloud';  // CSS选择器会自动匹配#game-map-container .cloud
        
        // 随机大小，根据容器尺寸调整
        const maxSize = Math.min(containerWidth, containerHeight) * 0.6;
        const size = FogConfig.minCloudSize + Math.random() * maxSize;
        cloud.style.width = `${size}px`;
        cloud.style.height = `${size}px`;
        
        // 随机位置，确保覆盖整个容器
        cloud.style.left = `${Math.random() * 120 - 10}%`;
        cloud.style.top = `${Math.random() * 120 - 10}%`;
        
        // 随机动画
        const duration = FogConfig.minAnimationDuration + Math.random() * 
            (FogConfig.maxAnimationDuration - FogConfig.minAnimationDuration);
        cloud.style.animation = `floatCloud ${duration}s infinite ease-in-out`;
        cloud.style.animationDelay = `${Math.random() * 8}s`;
        
        // 随机不透明度
        cloud.style.opacity = 0.7 + Math.random() * 0.3;
        
        container.appendChild(cloud);
    }
}

/**
 * 创建迷雾地图容器
 * @param {string} mapType - 迷雾类型，"cloud"表示云雾效果，"gradient"表示渐变迷雾效果
 * @returns {HTMLElement} 创建的地图容器元素
 */
function createFogMapContainer(mapType = "cloud") {
    // 创建地图容器，确保填满整个父容器
    const mapContainer = document.createElement("div");
    mapContainer.className = "map-container";  // CSS选择器会自动匹配#game-map-container .map-container
    mapContainer.style.width = "100%";
    mapContainer.style.height = "100%";
    mapContainer.style.position = "absolute";
    mapContainer.style.top = "0";
    mapContainer.style.left = "0";
    
    // 添加标题
    const titleDiv = document.createElement("div");
    titleDiv.className = "map-title";  // CSS选择器会自动匹配#game-map-container .map-title
    titleDiv.textContent = "北\n↑";
    mapContainer.appendChild(titleDiv);
    
    // 添加内容
    const contentDiv = document.createElement("div");
    contentDiv.className = "map-content";  // CSS选择器会自动匹配#game-map-container .map-content
    
    const messageDiv = document.createElement("div");
    messageDiv.className = "map-message";  // CSS选择器会自动匹配#game-map-container .map-message
    messageDiv.textContent = "【迷雾笼罩】";
    contentDiv.appendChild(messageDiv);
    
    mapContainer.appendChild(contentDiv);
    
    // 根据类型添加不同的迷雾效果
    if (mapType === "cloud") {
        // 添加云雾容器，确保完全覆盖
        const cloudFogDiv = document.createElement("div");
        cloudFogDiv.className = "cloud-fog";  // CSS选择器会自动匹配#game-map-container .cloud-fog
        cloudFogDiv.id = "cloud-fog-container";
        cloudFogDiv.style.width = "100%";
        cloudFogDiv.style.height = "100%";
        cloudFogDiv.style.position = "absolute";
        cloudFogDiv.style.top = "0";
        cloudFogDiv.style.left = "0";
        mapContainer.appendChild(cloudFogDiv);
        
        // 创建云朵
        createClouds(cloudFogDiv);
    } else {
        // 使用旧的迷雾效果，确保完全覆盖
        const fogDiv = document.createElement("div");
        fogDiv.className = "fog";  // CSS选择器会自动匹配#game-map-container .fog
        fogDiv.style.width = "100%";
        fogDiv.style.height = "100%";
        fogDiv.style.position = "absolute";
        fogDiv.style.top = "0";
        fogDiv.style.left = "0";
        mapContainer.appendChild(fogDiv);
    }
    
    return mapContainer;
}

/**
 * 渲染迷雾地图
 * @param {HTMLElement} targetElement - 目标元素，迷雾地图将被渲染到这个元素中
 */
function renderFogMap(targetElement) {
    // 清空目标元素
    targetElement.innerHTML = "";
    
    // 获取父容器（game-map-container）
    const parentContainer = targetElement.closest('#game-map-container');
    
    // 如果找不到父容器，直接使用目标元素
    const containerToUse = parentContainer || targetElement;
    
    // 创建迷雾地图容器
    const mapType = FogConfig.useCloudFogEffect ? "cloud" : "gradient";
    const mapContainer = createFogMapContainer(mapType);
    
    // 添加到目标元素
    targetElement.appendChild(mapContainer);
    
    // 确保目标元素填满父容器
    targetElement.style.width = "100%";
    targetElement.style.height = "100%";
    targetElement.style.position = "relative";
    targetElement.style.display = "block";
    
    // 调试信息
    console.log("渲染迷雾地图", {
        targetElement: targetElement.id,
        parentContainer: parentContainer ? parentContainer.id : "未找到",
        targetWidth: targetElement.offsetWidth,
        targetHeight: targetElement.offsetHeight,
        parentWidth: parentContainer ? parentContainer.offsetWidth : 0,
        parentHeight: parentContainer ? parentContainer.offsetHeight : 0
    });
}

/**
 * 初始化迷雾效果模块
 * 在页面加载完成后自动调用
 */
function initFogEffect() {
    console.log("迷雾效果模块初始化完成");
    
    // 监听窗口大小变化，重新调整迷雾效果
    window.addEventListener('resize', function() {
        const gameMapEl = document.getElementById("game-map");
        if (gameMapEl && gameMapEl.innerHTML.includes("map-container")) {
            // 如果当前显示的是迷雾地图，重新渲染
            renderFogMap(gameMapEl);
        }
    });
}

// 当页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initFogEffect);

// 导出模块
window.FogEffect = {
    config: FogConfig,
    renderFogMap: renderFogMap,
    createFogMapContainer: createFogMapContainer,
    createClouds: createClouds
}; 