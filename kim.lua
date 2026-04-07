task.spawn(function() 
    local VirtualInputManager = game:GetService("VirtualInputManager")
    _G.AntiStuckLoop = true 
    
    while _G.AntiStuckLoop do
        
        VirtualInputManager:SendKeyEvent(true, Enum.KeyCode.W, false, game)
        VirtualInputManager:SendKeyEvent(true, Enum.KeyCode.D, false, game)
        task.wait(0.5)
        VirtualInputManager:SendKeyEvent(false, Enum.KeyCode.D, false, game)
        
        
        VirtualInputManager:SendKeyEvent(true, Enum.KeyCode.A, false, game)
        task.wait(0.5)
        
        
        VirtualInputManager:SendKeyEvent(false, Enum.KeyCode.W, false, game)
        VirtualInputManager:SendKeyEvent(false, Enum.KeyCode.A, false, game)
        
        
        task.wait(0.7) 
    end
end)
local HITBOX_SIZE = 36
local HITBOX_TRANSPARENCY = 0.5

task.spawn(function() 
    while task.wait(0.5) do
        pcall(function()
            -- Thay đổi hitbox của quái
            for _, v in pairs(game.Workspace.Enemies:GetChildren()) do
                if v:FindFirstChild("HumanoidRootPart") then
                    v.HumanoidRootPart.Size = Vector3.new(HITBOX_SIZE, HITBOX_SIZE, HITBOX_SIZE)
                    v.HumanoidRootPart.Transparency = HITBOX_TRANSPARENCY
                    v.HumanoidRootPart.CanCollide = false
                end
            end

            -- Thay đổi hitbox của người chơi khác
            for _, p in pairs(game.Players:GetPlayers()) do
                if p ~= game.Players.LocalPlayer and p.Character and p.Character:FindFirstChild("HumanoidRootPart") then
                    p.Character.HumanoidRootPart.Size = Vector3.new(HITBOX_SIZE, HITBOX_SIZE, HITBOX_SIZE)
                    p.Character.HumanoidRootPart.Transparency = HITBOX_TRANSPARENCY
                    p.Character.HumanoidRootPart.CanCollide = false
                end
            end
        end)
    end
end)

spawn(function()
    local Players = game:GetService("Players")
    local RunService = game:GetService("RunService")
    local lp = Players.LocalPlayer
    local lastJump = 0

    RunService.RenderStepped:Connect(function()
        local char = lp.Character
        if not char then return end
        local root = char:FindFirstChild("HumanoidRootPart")
        local humanoid = char:FindFirstChild("Humanoid")
        if not root or not humanoid then return end

        local cam = workspace.CurrentCamera
        local goal = CFrame.new(root.Position + Vector3.new(0, 4.5, 0)) * root.CFrame.Rotation * CFrame.new(0, 10, 30)
        cam.CFrame = cam.CFrame:Lerp(goal, 0.2)

        if tick() - lastJump >= 3 then
            humanoid.Jump = true
            lastJump = tick()
        end
    end)
end)

loadstring(game:HttpGet("https://raw.githubusercontent.com/SkibidiHub111/.lua/refs/heads/main/moudlefastattack"))() 
loadstring(game:HttpGet("https://raw.githubusercontent.com/AnhDangNhoEm/TuanAnhIOS/refs/heads/main/koby"))()

-- [[ KHỞI TẠO BIẾN HỆ THỐNG ]]
local lp = game:GetService("Players").LocalPlayer
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Net = ReplicatedStorage:FindFirstChild("Net") -- Remote chính của Blox Fruit

-- Cấu hình mặc định (Nếu chưa có trong Script chính)
getgenv().AutoBounty = getgenv().AutoBounty or {}
getgenv().AutoBounty.Combat = getgenv().AutoBounty.Combat or {
    FastAttackSpeed = 15 -- Tốc độ đánh (1-15 là an toàn)
}

-- [[ HÀM KIỂM TRA TRÁI ÁC QUỶ ]]
function HasM1Fruit()
    local char = lp.Character
    local tool = char and char:FindFirstChildOfClass("Tool")
    -- Kiểm tra ToolTip là Blox Fruit
    if tool and tool.ToolTip == "Blox Fruit" then
        return true
    end
    return false
end

-- [[ HÀM FAST ATTACK M1 ]]
function FastAttackFruit()
    if getgenv().IsUsingFastAttack then return end
    
    local char = lp.Character
    local tool = char and char:FindFirstChildOfClass("Tool")
    
    if tool and HasM1Fruit() then
        getgenv().IsUsingFastAttack = true
        
        -- Số lần vung đòn trong 1 lần gọi hàm
        local attackSpeed = getgenv().AutoBounty.Combat.FastAttackSpeed or 12
        
        for i = 1, attackSpeed do
            task.spawn(function()
                pcall(function()
                    -- 1. Kích hoạt hiệu ứng vung tay
                    tool:Activate()
                    
                    -- 2. Gửi tín hiệu sát thương (Remote đánh thường)
                    local remote = tool:FindFirstChild("LeftClickRemote") or tool:FindFirstChild("Remote")
                    if remote then
                        remote:FireServer(Vector3.new(0,0,0), 1)
                    end
                    
                    -- 3. Gửi tín hiệu Attack lên Server (Gây dmg diện rộng)
                    if Net and getgenv().targ and getgenv().targ.Character then
                        Net:InvokeServer("Attack", {
                            [1] = getgenv().targ.Character:FindFirstChild("HumanoidRootPart")
                        })
                    end
                end)
            end)
            -- Delay cực nhỏ để tối ưu hóa tốc độ gửi gói tin (Packet)
            task.wait(0.005) 
        end
        
        getgenv().IsUsingFastAttack = false
    end
end

-- [[ VÒNG LẶP KÍCH HOẠT ]]
-- Script sẽ liên tục kiểm tra, nếu bạn đang cầm Fruit và có mục tiêu (targ), nó sẽ tự đánh.
task.spawn(function()
    while task.wait() do
        -- Chỉ chạy khi có mục tiêu (getgenv().targ)
        if getgenv().targ and HasM1Fruit() then
            FastAttackFruit()
        end
    end
end)