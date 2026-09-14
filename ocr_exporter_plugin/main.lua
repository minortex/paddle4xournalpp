-- ###################################################################################
-- # Xournal++ Linux OCR Plugin (Konsole 交互版)
-- # ###################################################################################

-- [配置区域]
local OCR_BINARY = "/home/texsd/.local/bin/pdf-ocr"

-- ###################################################################################
-- # 1. 插件初始化
-- # ###################################################################################

function initUi()
	app.registerUi({
		["menu"] = "执行 OCR (在 Konsole 中查看)",
		["callback"] = "startOcr",
	})
end

-- ###################################################################################
-- # 2. 核心逻辑
-- # ###################################################################################

function startOcr()
	-- 获取文档结构信息
	local doc = app.getDocumentStructure()
	local xoppPath = doc.xoppFilename

	local suggested
	if xoppPath ~= "" and xoppPath ~= nil then
		suggested = xoppPath:gsub("%.xopp$", ""):gsub("%.xoj$", "") .. "_ocr.pdf"
	else
		suggested = "/tmp/ocr_result.pdf"
	end

	-- 弹出保存对话框
	app.fileDialogSave("onPathSelected", suggested)
end

function onPathSelected(finalPath)
	if finalPath == "" or finalPath == nil then
		return
	end

	-- 使用时间戳防止文件名冲突
	local timestamp = os.time()
	local inputPdf = "/tmp/xpp_ocr_in_" .. timestamp .. ".pdf"

	-- 1. 导出当前文档
	app.export({ ["outputFile"] = inputPdf, ["background"] = "all" })

	-- 2. 构建 Konsole 命令行
	-- --noclose: 运行结束后不立即关闭窗口，方便查看结果
	-- -e: 执行后面的指令
	-- 指令链逻辑：执行 OCR -> 无论成功与否都删除临时 PDF -> 打印结束语
	local internalCmd = string.format(
		'%s --input "%s" --output "%s"; rm -f "%s"; echo "-----------------------"; echo "处理完成。按下任意按键退出。";read -n 1 -s -r',
		OCR_BINARY,
		inputPdf,
		finalPath,
		inputPdf
	)

	local shellCmd = string.format("konsole -e bash -c '%s' &", internalCmd)

	-- 3. 执行系统命令
	os.execute(shellCmd)
end
