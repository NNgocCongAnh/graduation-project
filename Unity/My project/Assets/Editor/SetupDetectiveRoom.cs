using UnityEngine;
using UnityEngine.UI;
using UnityEditor;
using UnityEditor.SceneManagement;

public class SetupDetectiveRoom : Editor
{
    [MenuItem("Detective Game/Setup 16:9 Noir Detective Room")]
    public static void Build169DetectiveRoom()
    {
        Debug.Log("[SetupDetectiveRoom] Reconstructing 16:9 Noir Detective Room with Diegetic Props & Depth...");

        // Ensure SampleScene is opened
        if (EditorSceneManager.GetActiveScene().path != "Assets/Scenes/SampleScene.unity")
        {
            EditorSceneManager.OpenScene("Assets/Scenes/SampleScene.unity");
        }

        // 1. Ensure Textures are imported properly as Sprites
        ConfigureAllTextures();

        // 2. Ensure EventSystem exists and uses New Input System
        EnsureEventSystem();

        // 3. Ensure [GameManagers] exists with all core scripts
        GameObject managersObj = EnsureGameManagers();

        // 4. Ensure Detective_UI_Canvas exists
        GameObject canvasObj = EnsureCanvas();
        Undo.RegisterFullObjectHierarchyUndo(canvasObj, "Setup 16:9 Noir Detective Room");

        // 5. Cache or create modals and card template
        GameObject cardTemplateObj = EnsureCardTemplate(canvasObj.transform);
        GameObject modalDetailObj = EnsureEvidenceDetailModal(canvasObj.transform);
        GameObject modalAccuseObj = EnsureAccusationModal(canvasObj.transform);
        GameObject modalAutopsyObj = EnsureAutopsyReportModal(canvasObj.transform);
        GameObject modalGenCaseObj = EnsureGenerateCaseModal(canvasObj.transform);

        // Detach modals & template temporarily so cleanup doesn't delete them
        cardTemplateObj.transform.SetParent(null);
        modalDetailObj.transform.SetParent(null);
        modalAccuseObj.transform.SetParent(null);
        modalAutopsyObj.transform.SetParent(null);
        modalGenCaseObj.transform.SetParent(null);

        // Clean up old canvas children
        while (canvasObj.transform.childCount > 0)
        {
            DestroyImmediate(canvasObj.transform.GetChild(0).gameObject);
        }

        // Configure Canvas Scaler to 1920x1080 (16:9)
        CanvasScaler scaler = canvasObj.GetComponent<CanvasScaler>();
        if (scaler != null)
        {
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.matchWidthOrHeight = 0.5f;
        }

        // Letterbox Cinema Black Background (handles ultrawide / 16:10 / 4:3)
        GameObject letterboxBg = CreateUIElement("Cinema_Letterbox_Bg", canvasObj.transform);
        Image letterboxImg = letterboxBg.AddComponent<Image>();
        letterboxImg.color = Color.black;
        letterboxImg.raycastTarget = false;
        StretchToParent(letterboxBg.GetComponent<RectTransform>());

        // 16:9 Viewport Root with AspectRatioFitter
        GameObject vp169 = CreateUIElement("Viewport_16_9_Room", canvasObj.transform);
        RectTransform vpRt = vp169.GetComponent<RectTransform>();
        StretchToParent(vpRt);
        AspectRatioFitter arf = vp169.AddComponent<AspectRatioFitter>();
        arf.aspectMode = AspectRatioFitter.AspectMode.FitInParent;
        arf.aspectRatio = 16f / 9f;
        vp169.AddComponent<RectMask2D>();

        // -------------------------------------------------------------
        // LAYER 0: ROOM WALL (Far Background)
        // -------------------------------------------------------------
        GameObject wallLayer = CreateUIElement("Layer_0_OfficeWall", vp169.transform);
        RectTransform wallRt = wallLayer.GetComponent<RectTransform>();
        StretchToParent(wallRt);
        wallRt.sizeDelta = new Vector2(140, 140);
        Image wallImg = wallLayer.AddComponent<Image>();
        wallImg.color = new Color(0.09f, 0.08f, 0.07f);
        wallImg.raycastTarget = false;

        // Venetian Blinds Shadow Stripes (Noir shadow bars)
        for (int i = 0; i < 8; i++)
        {
            GameObject blindStripe = CreateUIElement("Blind_Shadow_" + i, wallLayer.transform);
            Image bImg = blindStripe.AddComponent<Image>();
            bImg.color = new Color(0.03f, 0.02f, 0.02f, 0.45f);
            bImg.raycastTarget = false;
            RectTransform bRt = blindStripe.GetComponent<RectTransform>();
            bRt.anchorMin = new Vector2(0, 0.12f + (i * 0.11f));
            bRt.anchorMax = new Vector2(1, 0.18f + (i * 0.11f));
            bRt.offsetMin = Vector2.zero;
            bRt.offsetMax = Vector2.zero;
        }

        // Filing Cabinet silhouette in left corner
        GameObject cabinet = CreateUIElement("Filing_Cabinet_Corner", wallLayer.transform);
        Image cabImg = cabinet.AddComponent<Image>();
        cabImg.color = new Color(0.05f, 0.04f, 0.03f);
        cabImg.raycastTarget = false;
        RectTransform cabRt = cabinet.GetComponent<RectTransform>();
        cabRt.anchorMin = new Vector2(0, 0.15f);
        cabRt.anchorMax = new Vector2(0.12f, 0.85f);
        cabRt.offsetMin = Vector2.zero;
        cabRt.offsetMax = Vector2.zero;

        // -------------------------------------------------------------
        // LAYER 1: CORKBOARD RIG (Center Depth Layer)
        // -------------------------------------------------------------
        GameObject boardRig = CreateUIElement("Layer_1_Corkboard_Rig", vp169.transform);
        RectTransform boardRigRt = boardRig.GetComponent<RectTransform>();
        boardRigRt.anchorMin = new Vector2(0.5f, 0.58f);
        boardRigRt.anchorMax = new Vector2(0.5f, 0.58f);
        boardRigRt.sizeDelta = new Vector2(1540, 710);
        boardRigRt.anchoredPosition = Vector2.zero;

        // Deep Drop Shadow behind Corkboard
        GameObject dropShadow = CreateUIElement("Board_DropShadow", boardRig.transform);
        Image shadowImg = dropShadow.AddComponent<Image>();
        shadowImg.color = new Color(0, 0, 0, 0.72f);
        shadowImg.raycastTarget = false;
        RectTransform shadowRt = dropShadow.GetComponent<RectTransform>();
        StretchToParent(shadowRt);
        shadowRt.anchoredPosition = new Vector2(16, -22);

        // Mahogany Frame with Rich Wood Texture
        GameObject outerFrame = CreateUIElement("Board_OuterFrame", boardRig.transform);
        Image frameImg = outerFrame.AddComponent<Image>();
        Sprite woodSprite = LoadSprite("wood_frame_mahogany.png");
        if (woodSprite != null)
        {
            frameImg.sprite = woodSprite;
            frameImg.type = Image.Type.Tiled;
            frameImg.color = new Color(0.85f, 0.75f, 0.70f);
        }
        else
        {
            frameImg.color = new Color(0.20f, 0.12f, 0.07f);
        }
        frameImg.raycastTarget = false;
        StretchToParent(outerFrame.GetComponent<RectTransform>());

        // Inner Wood Bevel (Dark carved relief)
        GameObject innerBorder = CreateUIElement("Board_InnerBevel", outerFrame.transform);
        Image bevelImg = innerBorder.AddComponent<Image>();
        bevelImg.color = new Color(0.12f, 0.07f, 0.04f);
        bevelImg.raycastTarget = false;
        RectTransform bevelRt = innerBorder.GetComponent<RectTransform>();
        StretchToParent(bevelRt);
        bevelRt.offsetMin = new Vector2(16, 16);
        bevelRt.offsetMax = new Vector2(-16, -16);

        // Cork Surface - High-Res Seamless Cork Texture
        GameObject corkSurface = CreateUIElement("Cork_Surface", innerBorder.transform);
        RawImage corkImg = corkSurface.AddComponent<RawImage>();
        Texture2D corkTex = LoadTexture("cork_seamless.png", true);
        if (corkTex != null)
        {
            corkImg.texture = corkTex;
            corkImg.uvRect = new Rect(0, 0, 3.8f, 1.8f); // Seamless 3.8x1.8 tiling
            corkImg.color = Color.white;
        }
        else
        {
            corkImg.color = new Color(0.38f, 0.26f, 0.17f);
        }
        corkImg.raycastTarget = true;
        RectTransform corkRt = corkSurface.GetComponent<RectTransform>();
        StretchToParent(corkRt);
        corkRt.offsetMin = new Vector2(6, 6);
        corkRt.offsetMax = new Vector2(-6, -6);

        // Pin Card Container
        GameObject cardContainer = CreateUIElement("Card_Container", corkSurface.transform);
        StretchToParent(cardContainer.GetComponent<RectTransform>());

        // -------------------------------------------------------------
        // LAYER 2: FOREGROUND DETECTIVE DESK
        // -------------------------------------------------------------
        GameObject deskLayer = CreateUIElement("Layer_2_DetectiveDesk", vp169.transform);
        RectTransform deskRt = deskLayer.GetComponent<RectTransform>();
        deskRt.anchorMin = new Vector2(0, 0);
        deskRt.anchorMax = new Vector2(1, 0.22f);
        deskRt.offsetMin = new Vector2(-60, 0);
        deskRt.offsetMax = new Vector2(60, 0);

        Image deskImg = deskLayer.AddComponent<Image>();
        Sprite deskWoodSprite = LoadSprite("desk_surface_wood.png");
        if (deskWoodSprite != null)
        {
            deskImg.sprite = deskWoodSprite;
            deskImg.type = Image.Type.Tiled;
            deskImg.color = new Color(0.65f, 0.58f, 0.52f);
        }
        else
        {
            deskImg.color = new Color(0.13f, 0.09f, 0.06f);
        }
        deskImg.raycastTarget = false;

        // Desk Bevel Highlight Edge
        GameObject deskBevel = CreateUIElement("Desk_Bevel_Edge", deskLayer.transform);
        Image deskBevelImg = deskBevel.AddComponent<Image>();
        deskBevelImg.color = new Color(0.30f, 0.22f, 0.15f);
        deskBevelImg.raycastTarget = false;
        RectTransform dbRt = deskBevel.GetComponent<RectTransform>();
        dbRt.anchorMin = new Vector2(0, 1);
        dbRt.anchorMax = new Vector2(1, 1);
        dbRt.pivot = new Vector2(0.5f, 1);
        dbRt.sizeDelta = new Vector2(0, 4);

        // -------------------------------------------------------------
        // DIEGETIC PROPS ON DESK
        // -------------------------------------------------------------

        // 1. MANILA DOSSIER FOLDER (Trapezoid Perspective Shape)
        GameObject dossierObj = CreateUIElement("Manila_Dossier_Folder", deskLayer.transform);
        RectTransform dosRt = dossierObj.GetComponent<RectTransform>();
        dosRt.anchorMin = new Vector2(0.04f, 0.05f);
        dosRt.anchorMax = new Vector2(0.23f, 0.96f);
        dosRt.offsetMin = Vector2.zero;
        dosRt.offsetMax = Vector2.zero;
        dosRt.localRotation = Quaternion.Euler(0, 0, 2.5f); // Natural casual desk rotation

        Image dosImg = dossierObj.AddComponent<Image>();
        Sprite manilaSprite = LoadSprite("manila_dossier_trapezoid.png");
        if (manilaSprite != null)
        {
            dosImg.sprite = manilaSprite;
        }
        else
        {
            dosImg.color = new Color(0.68f, 0.55f, 0.36f);
        }
        dosImg.raycastTarget = false;

        GameObject dosTextObj = CreateUIElement("Label", dossierObj.transform);
        Text dosTxt = dosTextObj.AddComponent<Text>();
        dosTxt.text = "CONFIDENTIAL DOSSIER\nCASE #2026-001\n<size=9>BLACKWOOD MANOR</size>";
        dosTxt.fontSize = 11;
        dosTxt.fontStyle = FontStyle.Bold;
        dosTxt.color = new Color(0.24f, 0.18f, 0.13f);
        dosTxt.alignment = TextAnchor.MiddleCenter;
        dosTxt.raycastTarget = false;
        RectTransform dosTxtRt = dosTextObj.GetComponent<RectTransform>();
        StretchToParent(dosTxtRt);
        dosTxtRt.offsetMin = new Vector2(24, 18);
        dosTxtRt.offsetMax = new Vector2(-65, -22);

        // 2. CORONER'S AUTOPSY REPORT FOLDER (Forensic Henssge Report Trigger)
        GameObject autopsyFolderObj = CreateUIElement("Coroner_Autopsy_Folder_Btn", deskLayer.transform);
        RectTransform afRt = autopsyFolderObj.GetComponent<RectTransform>();
        afRt.anchorMin = new Vector2(0.24f, 0.05f);
        afRt.anchorMax = new Vector2(0.43f, 0.96f);
        afRt.offsetMin = Vector2.zero;
        afRt.offsetMax = Vector2.zero;
        afRt.localRotation = Quaternion.Euler(0, 0, -1.5f);

        Image afImg = autopsyFolderObj.AddComponent<Image>();
        Sprite autopsySprite = LoadSprite("coroner_autopsy_folder.png");
        if (autopsySprite != null)
        {
            afImg.sprite = autopsySprite;
        }
        else
        {
            afImg.color = new Color(0.24f, 0.35f, 0.42f);
        }
        afImg.raycastTarget = true;
        Button coronerBtn = autopsyFolderObj.AddComponent<Button>();

        GameObject afLabelObj = CreateUIElement("Label", autopsyFolderObj.transform);
        Text afTxt = afLabelObj.AddComponent<Text>();
        afTxt.text = "HỒ SƠ PHÁP Y // AUTOPSY\n<size=9>KHÁM NGHIỆM TỬ THI</size>\n<size=8>NHIỆT HỌC HENSSGE</size>";
        afTxt.fontSize = 11;
        afTxt.fontStyle = FontStyle.Bold;
        afTxt.color = new Color(0.88f, 0.92f, 0.95f);
        afTxt.alignment = TextAnchor.MiddleCenter;
        afTxt.raycastTarget = false;
        RectTransform aflRt = afLabelObj.GetComponent<RectTransform>();
        StretchToParent(aflRt);
        aflRt.offsetMin = new Vector2(24, 18);
        aflRt.offsetMax = new Vector2(-60, -22);

        // 3. Ceramic Coffee Mug
        GameObject mugObj = CreateUIElement("Coffee_Mug", deskLayer.transform);
        Image mugImg = mugObj.AddComponent<Image>();
        mugImg.color = new Color(0.82f, 0.79f, 0.72f);
        mugImg.raycastTarget = false;
        RectTransform mugRt = mugObj.GetComponent<RectTransform>();
        mugRt.anchorMin = new Vector2(0.005f, 0.25f);
        mugRt.anchorMax = new Vector2(0.038f, 0.85f);
        mugRt.offsetMin = Vector2.zero;
        mugRt.offsetMax = Vector2.zero;

        // 4. ARREST WARRANT FOLDER (Trapezoid Perspective Shape + Accusation Button)
        GameObject warrantFolderObj = CreateUIElement("Arrest_Warrant_Folder_Btn", deskLayer.transform);
        RectTransform wfRt = warrantFolderObj.GetComponent<RectTransform>();
        wfRt.anchorMin = new Vector2(0.44f, 0.04f);
        wfRt.anchorMax = new Vector2(0.71f, 0.98f);
        wfRt.offsetMin = Vector2.zero;
        wfRt.offsetMax = Vector2.zero;
        wfRt.localRotation = Quaternion.Euler(0, 0, -2.0f); // Angled trapezoid lying on desk

        Image wfImg = warrantFolderObj.AddComponent<Image>();
        Sprite warrantSprite = LoadSprite("arrest_warrant_trapezoid.png");
        if (warrantSprite != null)
        {
            wfImg.sprite = warrantSprite;
        }
        else
        {
            wfImg.color = new Color(0.65f, 0.12f, 0.12f);
        }
        wfImg.raycastTarget = true;
        Button warrantBtn = warrantFolderObj.AddComponent<Button>();

        GameObject wfLabelObj = CreateUIElement("Label", warrantFolderObj.transform);
        Text wfTxt = wfLabelObj.AddComponent<Text>();
        wfTxt.text = "LỆNH BẮT GIỮ // ARREST WARRANT\n<size=12>CHỈ ĐỊNH THỦ PHẠM & NỘP CHỨNG CỨ</size>";
        wfTxt.fontSize = 13;
        wfTxt.fontStyle = FontStyle.Bold;
        wfTxt.color = new Color(0.96f, 0.92f, 0.82f);
        wfTxt.alignment = TextAnchor.MiddleCenter;
        wfTxt.raycastTarget = false;
        RectTransform wflRt = wfLabelObj.GetComponent<RectTransform>();
        StretchToParent(wflRt);
        wflRt.offsetMin = new Vector2(36, 16);
        wflRt.offsetMax = new Vector2(-88, -20);

        // 4. (Walkie-talkie removed - replaced by the Hotkey_Taskbar built after the chat panel)

        // 5. BANKER'S DESK LAMP WITH INTERACTIVE PULL-CHAIN
        GameObject lampObj = CreateUIElement("Bankers_Desk_Lamp", deskLayer.transform);
        RectTransform lampRt = lampObj.GetComponent<RectTransform>();
        lampRt.anchorMin = new Vector2(0.86f, 0.25f);
        lampRt.anchorMax = new Vector2(0.97f, 1.95f);
        lampRt.offsetMin = Vector2.zero;
        lampRt.offsetMax = Vector2.zero;

        // Lamp art keeps the sprite 180x280 aspect so chain anchors (in sprite pixels) line up.
        GameObject lampArtObj = CreateUIElement("Lamp_Art", lampObj.transform);
        StretchToParent(lampArtObj.GetComponent<RectTransform>());
        AspectRatioFitter lampFit = lampArtObj.AddComponent<AspectRatioFitter>();
        lampFit.aspectMode = AspectRatioFitter.AspectMode.FitInParent;
        lampFit.aspectRatio = 180f / 280f;

        // Pull chain is drawn BEFORE the body so its top beads hide behind the shade;
        // pulling it down reveals those beads instead of opening a gap.
        GameObject chainObj = CreateUIElement("Pull_Chain", lampArtObj.transform);
        RectTransform chainRt = chainObj.GetComponent<RectTransform>();
        chainRt.pivot = new Vector2(0.5f, 1f);
        chainRt.anchorMin = new Vector2(110f / 180f, 1f - 150f / 280f);
        chainRt.anchorMax = new Vector2(124f / 180f, 1f - 61f / 280f);
        chainRt.offsetMin = Vector2.zero;
        chainRt.offsetMax = Vector2.zero;
        Image chainImg = chainObj.AddComponent<Image>();
        chainImg.sprite = LoadSprite("bankers_lamp_chain.png");
        chainImg.raycastTarget = true;

        GameObject lampBodyObj = CreateUIElement("Lamp_Body", lampArtObj.transform);
        StretchToParent(lampBodyObj.GetComponent<RectTransform>());
        Image lampImg = lampBodyObj.AddComponent<Image>();
        Sprite lampSprite = LoadSprite("bankers_lamp_body.png");
        if (lampSprite != null)
        {
            lampImg.sprite = lampSprite;
        }
        else
        {
            lampImg.color = new Color(0.11f, 0.38f, 0.20f);
        }
        lampImg.raycastTarget = false;

        // -------------------------------------------------------------
        // LAYER 3: ATMOSPHERIC LIGHTING & VIGNETTE (NON-BLOCKING)
        // -------------------------------------------------------------
        // Soft Radial Spotlight Glow
        GameObject softLightObj = CreateUIElement("Layer_3_Soft_Spotlight", vp169.transform);
        Image softLightImg = softLightObj.AddComponent<Image>();
        Sprite lightSprite = LoadSprite("soft_radial_light.png");
        if (lightSprite != null)
        {
            softLightImg.sprite = lightSprite;
            softLightImg.color = new Color(1f, 0.92f, 0.68f, 0.38f);
        }
        else
        {
            softLightImg.color = new Color(1f, 0.85f, 0.45f, 0.05f);
        }
        softLightImg.raycastTarget = false; // NEVER BLOCK RAYCASTS!
        RectTransform slRt = softLightObj.GetComponent<RectTransform>();
        slRt.anchorMin = new Vector2(0.55f, 0.20f);
        slRt.anchorMax = new Vector2(1.05f, 0.95f);
        slRt.offsetMin = Vector2.zero;
        slRt.offsetMax = Vector2.zero;

        // Cinematic Vignette (Dark Corners)
        GameObject vignetteObj = CreateUIElement("Cinematic_Vignette", vp169.transform);
        Image vigImg = vignetteObj.AddComponent<Image>();
        vigImg.color = new Color(0, 0, 0, 0.32f);
        vigImg.raycastTarget = false; // NEVER BLOCK RAYCASTS!
        StretchToParent(vignetteObj.GetComponent<RectTransform>());

        // Generous Click Zone for Lamp & Chain (Easy to click anywhere on shade or cord)
        GameObject lampClickZone = CreateUIElement("Lamp_Click_Zone", lampObj.transform);
        Image clickZoneImg = lampClickZone.AddComponent<Image>();
        clickZoneImg.color = new Color(0, 0, 0, 0); // Completely transparent
        clickZoneImg.raycastTarget = true;
        RectTransform czRt = lampClickZone.GetComponent<RectTransform>();
        czRt.anchorMin = new Vector2(0.08f, 0.20f);
        czRt.anchorMax = new Vector2(0.96f, 0.98f);
        czRt.offsetMin = Vector2.zero;
        czRt.offsetMax = Vector2.zero;

        // Attach BankersLampController to Click Zone
        BankersLampController lampCtrl = lampClickZone.AddComponent<BankersLampController>();
        SerializedObject lSO = new SerializedObject(lampCtrl);
        lSO.FindProperty("chainTransform").objectReferenceValue = chainRt;
        lSO.FindProperty("lampShadeImage").objectReferenceValue = lampImg;
        lSO.FindProperty("softLightObject").objectReferenceValue = softLightObj;
        lSO.ApplyModifiedProperties();

        // -------------------------------------------------------------
        // LAYER 4: HUD & POLICE RADIO CHAT DISPATCH
        // -------------------------------------------------------------
        GameObject headerObj = CreateUIElement("Header_Panel", vp169.transform);
        Image headerImg = headerObj.AddComponent<Image>();
        headerImg.color = new Color(0.06f, 0.05f, 0.04f, 0.92f);
        headerImg.raycastTarget = false;
        RectTransform headerRt = headerObj.GetComponent<RectTransform>();
        headerRt.anchorMin = new Vector2(0, 1);
        headerRt.anchorMax = new Vector2(1, 1);
        headerRt.pivot = new Vector2(0.5f, 1);
        headerRt.sizeDelta = new Vector2(0, 56);
        headerRt.anchoredPosition = Vector2.zero;

        GameObject titleObj = CreateUIElement("Case_Title_Text", headerObj.transform);
        Text titleTxt = titleObj.AddComponent<Text>();
        titleTxt.text = "PHÒNG ĐIỀU TRA // CASE #2026-001: BÍ ẨN BIỆT THỰ BLACKWOOD";
        titleTxt.fontSize = 18;
        titleTxt.fontStyle = FontStyle.Bold;
        titleTxt.alignment = TextAnchor.MiddleLeft;
        titleTxt.color = new Color(0.92f, 0.86f, 0.74f);
        titleTxt.raycastTarget = false;
        RectTransform titleRt = titleObj.GetComponent<RectTransform>();
        titleRt.anchorMin = new Vector2(0, 0);
        titleRt.anchorMax = new Vector2(0.58f, 1);
        titleRt.offsetMin = new Vector2(26, 0);
        titleRt.offsetMax = Vector2.zero;

        // Button to Open AI Case Generator Modal
        GameObject btnNewCaseObj = CreateButton("Btn_New_Case", headerObj.transform, "+ TẠO VỤ ÁN MỚI", new Color(0.12f, 0.48f, 0.32f));
        Button btnNewCase = btnNewCaseObj.GetComponent<Button>();
        RectTransform bncRt = btnNewCaseObj.GetComponent<RectTransform>();
        bncRt.anchorMin = new Vector2(0.60f, 0.16f);
        bncRt.anchorMax = new Vector2(0.76f, 0.84f);
        bncRt.offsetMin = Vector2.zero;
        bncRt.offsetMax = Vector2.zero;

        GameObject badgeObj = CreateUIElement("Badge", headerObj.transform);
        Image badgeImg = badgeObj.AddComponent<Image>();
        badgeImg.color = new Color(0.62f, 0.12f, 0.12f);
        badgeImg.raycastTarget = false;
        RectTransform badgeRt = badgeObj.GetComponent<RectTransform>();
        badgeRt.anchorMin = new Vector2(0.78f, 0.18f);
        badgeRt.anchorMax = new Vector2(0.98f, 0.82f);
        badgeRt.offsetMin = Vector2.zero;
        badgeRt.offsetMax = Vector2.zero;

        GameObject badgeTxtObj = CreateUIElement("Text", badgeObj.transform);
        Text badgeTxt = badgeTxtObj.AddComponent<Text>();
        badgeTxt.text = "UNDER INVESTIGATION";
        badgeTxt.fontSize = 12;
        badgeTxt.fontStyle = FontStyle.Bold;
        badgeTxt.color = Color.white;
        badgeTxt.alignment = TextAnchor.MiddleCenter;
        badgeTxt.raycastTarget = false;
        StretchToParent(badgeTxtObj.GetComponent<RectTransform>());

        // -------------------------------------------------------------
        // POLICE RADIO CHAT DISPATCH PANEL
        // -------------------------------------------------------------
        GameObject chatPanel = CreateUIElement("Police_Radio_Chat_Panel", vp169.transform);
        Image cpImg = chatPanel.AddComponent<Image>();
        cpImg.color = new Color(0.08f, 0.09f, 0.10f, 0.95f);
        RectTransform cpRt = chatPanel.GetComponent<RectTransform>();
        cpRt.anchorMin = new Vector2(0.65f, 0.23f);
        cpRt.anchorMax = new Vector2(0.98f, 0.70f);
        cpRt.offsetMin = Vector2.zero;
        cpRt.offsetMax = Vector2.zero;

        // Chat Header
        GameObject cpHeader = CreateUIElement("Header", chatPanel.transform);
        Image cphImg = cpHeader.AddComponent<Image>();
        cphImg.color = new Color(0.14f, 0.16f, 0.18f);
        RectTransform cphRt = cpHeader.GetComponent<RectTransform>();
        cphRt.anchorMin = new Vector2(0, 1);
        cphRt.anchorMax = new Vector2(1, 1);
        cphRt.pivot = new Vector2(0.5f, 1);
        cphRt.sizeDelta = new Vector2(0, 35);
        cphRt.anchoredPosition = Vector2.zero;

        GameObject cpTitle = CreateUIElement("Title", cpHeader.transform);
        Text cptTxt = cpTitle.AddComponent<Text>();
        cptTxt.text = "POLICE RADIO // DISPATCH LOG";
        cptTxt.fontSize = 12;
        cptTxt.fontStyle = FontStyle.Bold;
        cptTxt.color = new Color(0.9f, 0.85f, 0.75f);
        cptTxt.alignment = TextAnchor.MiddleLeft;
        RectTransform cptRt = cpTitle.GetComponent<RectTransform>();
        StretchToParent(cptRt);
        cptRt.offsetMin = new Vector2(12, 0);

        GameObject cpCloseBtn = CreateButton("Btn_Close_Chat", cpHeader.transform, "X", new Color(0.6f, 0.15f, 0.15f));
        RectTransform cpcRt = cpCloseBtn.GetComponent<RectTransform>();
        cpcRt.anchorMin = new Vector2(1, 0.5f);
        cpcRt.anchorMax = new Vector2(1, 0.5f);
        cpcRt.pivot = new Vector2(1, 0.5f);
        cpcRt.sizeDelta = new Vector2(28, 26);
        cpcRt.anchoredPosition = new Vector2(-6, 0);

        // Chat Log Text Area
        GameObject logObj = CreateUIElement("Chat_Log_Text", chatPanel.transform);
        Text logTxt = logObj.AddComponent<Text>();
        logTxt.text = "Connecting to police dispatch frequency...";
        logTxt.fontSize = 12;
        logTxt.alignment = TextAnchor.LowerLeft;
        logTxt.color = new Color(0.88f, 0.88f, 0.88f);
        RectTransform logRt = logObj.GetComponent<RectTransform>();
        logRt.anchorMin = new Vector2(0, 0.18f);
        logRt.anchorMax = new Vector2(1, 1);
        logRt.offsetMin = new Vector2(12, 6);
        logRt.offsetMax = new Vector2(-12, -40);

        // Chat Input Box
        GameObject inputObj = CreateInputField("Chat_InputField", chatPanel.transform, "Transmit message to detectives...");
        RectTransform inRt = inputObj.GetComponent<RectTransform>();
        inRt.anchorMin = new Vector2(0, 0);
        inRt.anchorMax = new Vector2(0.74f, 0.15f);
        inRt.offsetMin = new Vector2(10, 8);
        inRt.offsetMax = Vector2.zero;

        // Send Button
        GameObject sendBtn = CreateButton("Btn_Send_Message", chatPanel.transform, "SEND", new Color(0.20f, 0.45f, 0.28f));
        RectTransform sRt = sendBtn.GetComponent<RectTransform>();
        sRt.anchorMin = new Vector2(0.76f, 0);
        sRt.anchorMax = new Vector2(1, 0.15f);
        sRt.offsetMin = new Vector2(4, 8);
        sRt.offsetMax = new Vector2(-10, 0);

        // Wire DetectiveChatUI
        DetectiveChatUI chatUI = chatPanel.GetComponent<DetectiveChatUI>();
        if (chatUI == null) chatUI = chatPanel.AddComponent<DetectiveChatUI>();
        SerializedObject chatSO = new SerializedObject(chatUI);
        chatSO.FindProperty("chatPanel").objectReferenceValue = chatPanel;
        chatSO.FindProperty("chatLogText").objectReferenceValue = logTxt;
        chatSO.FindProperty("chatInputField").objectReferenceValue = inputObj.GetComponent<InputField>();
        chatSO.FindProperty("sendButton").objectReferenceValue = sendBtn.GetComponent<Button>();
        chatSO.ApplyModifiedProperties();

        // Close button listener
        Button cpcBtn = cpCloseBtn.GetComponent<Button>();
        cpcBtn.onClick.AddListener(chatUI.ToggleChatPanel);

        // Chat panel starts closed
        chatPanel.SetActive(false);

        BuildHotkeyTaskbar(vp169.transform, headerObj.transform, titleTxt.font, chatUI);

        // -------------------------------------------------------------
        // RE-ATTACH MODALS & CARD TEMPLATE DIRECTLY ON CANVAS (PERFECT FULLSCREEN CENTER)
        // -------------------------------------------------------------
        cardTemplateObj.transform.SetParent(canvasObj.transform, false);
        cardTemplateObj.SetActive(false);

        // Center Evidence Detail Modal directly on Root Canvas
        modalDetailObj.transform.SetParent(canvasObj.transform, false);
        ResetModalTransform(modalDetailObj);
        modalDetailObj.SetActive(false);

        // Center Accusation Modal directly on Root Canvas
        modalAccuseObj.transform.SetParent(canvasObj.transform, false);
        ResetModalTransform(modalAccuseObj);
        modalAccuseObj.SetActive(false);

        AccusationModal accuseModal = modalAccuseObj.GetComponent<AccusationModal>();
        if (accuseModal != null)
        {
            Button btn = warrantBtn;
            while (btn.onClick.GetPersistentEventCount() > 0)
            {
                UnityEditor.Events.UnityEventTools.RemovePersistentListener(btn.onClick, 0);
            }
            UnityEditor.Events.UnityEventTools.AddPersistentListener(btn.onClick, accuseModal.Open);
        }

        // Center Coroner Autopsy Report Modal directly on Root Canvas
        modalAutopsyObj.transform.SetParent(canvasObj.transform, false);
        ResetModalTransform(modalAutopsyObj);
        modalAutopsyObj.SetActive(false);

        AutopsyReportModal autopsyModal = modalAutopsyObj.GetComponent<AutopsyReportModal>();
        if (autopsyModal != null)
        {
            Button btn = coronerBtn;
            while (btn.onClick.GetPersistentEventCount() > 0)
            {
                UnityEditor.Events.UnityEventTools.RemovePersistentListener(btn.onClick, 0);
            }
            UnityEditor.Events.UnityEventTools.AddPersistentListener(btn.onClick, autopsyModal.Open);
        }

        // Center AI Case Generator Modal directly on Root Canvas
        modalGenCaseObj.transform.SetParent(canvasObj.transform, false);
        ResetModalTransform(modalGenCaseObj);
        modalGenCaseObj.SetActive(false);

        GenerateCaseModal genCaseModal = modalGenCaseObj.GetComponent<GenerateCaseModal>();
        if (genCaseModal != null)
        {
            Button btn = btnNewCase;
            while (btn.onClick.GetPersistentEventCount() > 0)
            {
                UnityEditor.Events.UnityEventTools.RemovePersistentListener(btn.onClick, 0);
            }
            UnityEditor.Events.UnityEventTools.AddPersistentListener(btn.onClick, genCaseModal.Open);
        }

        // Attach DetectiveRoomParallax
        DetectiveRoomParallax parallax = vp169.GetComponent<DetectiveRoomParallax>();
        if (parallax == null) parallax = vp169.AddComponent<DetectiveRoomParallax>();
        SerializedObject pSO = new SerializedObject(parallax);
        pSO.FindProperty("wallLayer").objectReferenceValue = wallRt;
        pSO.FindProperty("corkboardLayer").objectReferenceValue = boardRigRt;
        pSO.FindProperty("deskLayer").objectReferenceValue = deskRt;
        pSO.FindProperty("lightConeLayer").objectReferenceValue = slRt;
        pSO.ApplyModifiedProperties();

        // Update CorkboardManager references to new Card_Container and cardPrefab
        if (managersObj != null)
        {
            CorkboardManager corkboard = managersObj.GetComponent<CorkboardManager>();
            if (corkboard != null)
            {
                SerializedObject cSO = new SerializedObject(corkboard);
                cSO.FindProperty("itemContainer").objectReferenceValue = cardContainer.transform;
                cSO.FindProperty("cardPrefab").objectReferenceValue = cardTemplateObj;
                cSO.ApplyModifiedProperties();
            }

            GameController gc = managersObj.GetComponent<GameController>();
            if (gc != null)
            {
                SerializedObject gcSO = new SerializedObject(gc);
                gcSO.FindProperty("apiManager").objectReferenceValue = managersObj.GetComponent<DetectiveAPIManager>();
                gcSO.FindProperty("corkboardManager").objectReferenceValue = corkboard;
                gcSO.ApplyModifiedProperties();
            }
        }

        // Mark scene dirty and save
        EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
        EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene());
        Debug.Log("[SetupDetectiveRoom] 16:9 Noir Detective Investigation Room successfully generated with centered modals, interactive pull-chain lamp, and perspective trapezoid folders!");

        // Automatically capture high-res snapshot for visual inspection
        SceneVisualInspector.CaptureSnapshot();
    }

    private static void ResetModalTransform(GameObject modal)
    {
        if (modal == null) return;
        RectTransform rt = modal.GetComponent<RectTransform>();
        if (rt == null) return;

        rt.localScale = Vector3.one;
        rt.localRotation = Quaternion.identity;
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;
        rt.pivot = new Vector2(0.5f, 0.5f);
        rt.anchoredPosition = Vector2.zero;

        // Reset inner box
        string[] boxNames = new[] { "Accusation_Box", "Modal_Box", "Autopsy_Box", "Generator_Box" };
        foreach (var bName in boxNames)
        {
            Transform box = modal.transform.Find(bName);
            if (box != null)
            {
                RectTransform brt = box.GetComponent<RectTransform>();
                brt.localScale = Vector3.one;
                brt.localRotation = Quaternion.identity;
                brt.anchorMin = new Vector2(0.5f, 0.5f);
                brt.anchorMax = new Vector2(0.5f, 0.5f);
                brt.pivot = new Vector2(0.5f, 0.5f);
                brt.anchoredPosition = Vector2.zero;
            }
        }

        Transform vPanel = modal.transform.Find("Verdict_Panel");
        if (vPanel != null)
        {
            RectTransform vprt = vPanel.GetComponent<RectTransform>();
            vprt.localScale = Vector3.one;
            vprt.anchorMin = Vector2.zero;
            vprt.anchorMax = Vector2.one;
            vprt.offsetMin = Vector2.zero;
            vprt.offsetMax = Vector2.zero;
            vprt.anchoredPosition = Vector2.zero;

            Transform vBox = vPanel.Find("Verdict_Box");
            if (vBox != null)
            {
                RectTransform vbrt = vBox.GetComponent<RectTransform>();
                vbrt.localScale = Vector3.one;
                vbrt.anchorMin = new Vector2(0.5f, 0.5f);
                vbrt.anchorMax = new Vector2(0.5f, 0.5f);
                vbrt.pivot = new Vector2(0.5f, 0.5f);
                vbrt.anchoredPosition = Vector2.zero;
            }
        }
    }

    private static void ConfigureAllTextures()
    {
        string[] textures = new[] {
            "cork_seamless.png",
            "wood_frame_mahogany.png",
            "desk_surface_wood.png",
            "pushpin_3d.png",
            "paper_card_bg.png",
            "card_drop_shadow.png",
            "arrest_warrant_folder.png",
            "arrest_warrant_trapezoid.png",
            "manila_dossier_trapezoid.png",
            "coroner_autopsy_folder.png",
            "police_radio_90s.png",
            "bankers_lamp_prop.png",
            "soft_radial_light.png"
        };

        foreach (var tex in textures)
        {
            string path = "Assets/Textures/NoirUI/" + tex;
            TextureImporter ti = AssetImporter.GetAtPath(path) as TextureImporter;
            if (ti != null)
            {
                bool modified = false;
                if (ti.textureType != TextureImporterType.Sprite)
                {
                    ti.textureType = TextureImporterType.Sprite;
                    ti.spriteImportMode = SpriteImportMode.Single;
                    modified = true;
                }
                if (tex.Contains("cork_seamless") || tex.Contains("desk_surface_wood") || tex.Contains("wood_frame"))
                {
                    if (ti.wrapMode != TextureWrapMode.Repeat)
                    {
                        ti.wrapMode = TextureWrapMode.Repeat;
                        modified = true;
                    }
                }
                if (modified)
                {
                    ti.SaveAndReimport();
                }
            }
        }
        AssetDatabase.Refresh();
    }

    private static Sprite LoadSprite(string filename)
    {
        string path = "Assets/Textures/NoirUI/" + filename;
        return AssetDatabase.LoadAssetAtPath<Sprite>(path);
    }

    private static Texture2D LoadTexture(string filename, bool repeat = false)
    {
        string path = "Assets/Textures/NoirUI/" + filename;
        return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
    }

    private static void EnsureEventSystem()
    {
        GameObject esObj = GameObject.Find("EventSystem");
        if (esObj == null)
        {
            esObj = new GameObject("EventSystem");
            esObj.AddComponent<UnityEngine.EventSystems.EventSystem>();
            esObj.AddComponent<UnityEngine.InputSystem.UI.InputSystemUIInputModule>();
        }
        else
        {
            var legacyModule = esObj.GetComponent<UnityEngine.EventSystems.StandaloneInputModule>();
            if (legacyModule != null) DestroyImmediate(legacyModule);
            if (esObj.GetComponent<UnityEngine.InputSystem.UI.InputSystemUIInputModule>() == null)
            {
                esObj.AddComponent<UnityEngine.InputSystem.UI.InputSystemUIInputModule>();
            }
        }
    }

    private static GameObject EnsureGameManagers()
    {
        GameObject managersObj = GameObject.Find("[GameManagers]");
        if (managersObj == null)
        {
            managersObj = new GameObject("[GameManagers]");
            managersObj.AddComponent<DetectiveAPIManager>();
            managersObj.AddComponent<CorkboardManager>();
            managersObj.AddComponent<GameController>();
            managersObj.AddComponent<DetectiveNetworkManager>();
        }
        return managersObj;
    }

    private static GameObject EnsureCanvas()
    {
        GameObject canvasObj = GameObject.Find("Detective_UI_Canvas");
        if (canvasObj == null)
        {
            canvasObj = new GameObject("Detective_UI_Canvas");
            Canvas c = canvasObj.AddComponent<Canvas>();
            c.renderMode = RenderMode.ScreenSpaceOverlay;
            CanvasScaler cs = canvasObj.AddComponent<CanvasScaler>();
            cs.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            cs.referenceResolution = new Vector2(1920, 1080);
            cs.matchWidthOrHeight = 0.5f;
            canvasObj.AddComponent<GraphicRaycaster>();
        }
        return canvasObj;
    }

    public static GameObject EnsureCardTemplate(Transform canvasTransform)
    {
        Transform old = canvasTransform.Find("Polaroid_Card_Template");
        if (old == null) old = canvasTransform.Find("Viewport_16_9_Room/Polaroid_Card_Template");
        if (old != null) DestroyImmediate(old.gameObject);

        GameObject card = CreateUIElement("Polaroid_Card_Template", canvasTransform);
        RectTransform rt = card.GetComponent<RectTransform>();
        rt.sizeDelta = new Vector2(204, 252);

        // 1. Fake Drop Shadow Layer
        GameObject shadowObj = CreateUIElement("Card_Shadow", card.transform);
        Image shadowImg = shadowObj.AddComponent<Image>();
        Sprite shadowSprite = LoadSprite("card_drop_shadow.png");
        if (shadowSprite != null)
        {
            shadowImg.sprite = shadowSprite;
            shadowImg.color = new Color(0, 0, 0, 0.65f);
        }
        else
        {
            shadowImg.color = new Color(0, 0, 0, 0.45f);
        }
        shadowImg.raycastTarget = false;
        RectTransform sRt = shadowObj.GetComponent<RectTransform>();
        sRt.sizeDelta = new Vector2(216, 264);
        sRt.anchoredPosition = new Vector2(7, -9);

        // 2. Off-White Paper Body
        GameObject paperObj = CreateUIElement("Card_Paper_Body", card.transform);
        Image paperImg = paperObj.AddComponent<Image>();
        Sprite paperSprite = LoadSprite("paper_card_bg.png");
        if (paperSprite != null)
        {
            paperImg.sprite = paperSprite;
        }
        else
        {
            paperImg.color = new Color(0.96f, 0.95f, 0.92f);
        }
        paperImg.raycastTarget = true;
        StretchToParent(paperObj.GetComponent<RectTransform>());

        // 3. Photo Cutout with RectMask2D (Strict 1:1 interior crop)
        GameObject maskObj = CreateUIElement("Photo_Cutout_Mask", paperObj.transform);
        RectTransform maskRt = maskObj.GetComponent<RectTransform>();
        maskRt.sizeDelta = new Vector2(174, 174);
        maskRt.anchoredPosition = new Vector2(0, 24);
        maskObj.AddComponent<RectMask2D>();

        // Recessed inner shadow/border inside mask
        GameObject innerBorder = CreateUIElement("Photo_Recess_Border", paperObj.transform);
        Image ibImg = innerBorder.AddComponent<Image>();
        ibImg.color = new Color(0.12f, 0.10f, 0.08f, 0.25f);
        ibImg.raycastTarget = false;
        RectTransform ibRt = innerBorder.GetComponent<RectTransform>();
        ibRt.sizeDelta = new Vector2(176, 176);
        ibRt.anchoredPosition = new Vector2(0, 24);

        // Photo RawImage inside Mask
        GameObject photo = CreateUIElement("Photo_RawImage", maskObj.transform);
        RawImage photoImg = photo.AddComponent<RawImage>();
        photoImg.color = new Color(0.22f, 0.22f, 0.24f);
        photoImg.raycastTarget = false;
        RectTransform pRt = photo.GetComponent<RectTransform>();
        StretchToParent(pRt);

        // 4. Typewriter Title Label at bottom
        GameObject label = CreateUIElement("Label", paperObj.transform);
        Text labelTxt = label.AddComponent<Text>();
        labelTxt.text = "Clue / Suspect Name";
        labelTxt.fontSize = 12;
        labelTxt.fontStyle = FontStyle.Bold;
        labelTxt.alignment = TextAnchor.MiddleCenter;
        labelTxt.color = new Color(0.16f, 0.13f, 0.11f);
        labelTxt.raycastTarget = false;
        RectTransform lRt = label.GetComponent<RectTransform>();
        lRt.anchorMin = new Vector2(0, 0);
        lRt.anchorMax = new Vector2(1, 0.24f);
        lRt.offsetMin = new Vector2(8, 6);
        lRt.offsetMax = new Vector2(-8, -4);

        // 5. Glossy 3D Push-Pin at top
        GameObject pinObj = CreateUIElement("Push_Pin_3D", paperObj.transform);
        Image pinImg = pinObj.AddComponent<Image>();
        Sprite pinSprite = LoadSprite("pushpin_3d.png");
        if (pinSprite != null)
        {
            pinImg.sprite = pinSprite;
        }
        else
        {
            pinImg.color = new Color(0.85f, 0.18f, 0.18f);
        }
        pinImg.raycastTarget = false;
        RectTransform pinRt = pinObj.GetComponent<RectTransform>();
        pinRt.sizeDelta = new Vector2(28, 28);
        pinRt.anchoredPosition = new Vector2(0, 116);

        // Attach DraggableCard script to the card root
        DraggableCard draggable = card.GetComponent<DraggableCard>();
        if (draggable == null) draggable = card.AddComponent<DraggableCard>();

        card.SetActive(false);
        return card;
    }

    private static GameObject EnsureEvidenceDetailModal(Transform canvasTransform)
    {
        Transform existing = canvasTransform.Find("Evidence_Detail_Modal");
        if (existing == null) existing = canvasTransform.Find("Viewport_16_9_Room/Evidence_Detail_Modal");
        if (existing != null) DestroyImmediate(existing.gameObject);

        GameObject modal = CreateUIElement("Evidence_Detail_Modal", canvasTransform);
        StretchToParent(modal.GetComponent<RectTransform>());
        Image bg = modal.AddComponent<Image>();
        bg.color = new Color(0, 0, 0, 0.80f);

        GameObject box = CreateUIElement("Modal_Box", modal.transform);
        Image boxImg = box.AddComponent<Image>();
        boxImg.color = new Color(0.12f, 0.11f, 0.10f);
        RectTransform boxRt = box.GetComponent<RectTransform>();
        boxRt.sizeDelta = new Vector2(640, 520);
        boxRt.anchoredPosition = Vector2.zero;

        // Title
        GameObject titleObj = CreateUIElement("Title_Text", box.transform);
        Text titleTxt = titleObj.AddComponent<Text>();
        titleTxt.text = "BẰNG CHỨNG CHI TIẾT";
        titleTxt.fontSize = 20;
        titleTxt.fontStyle = FontStyle.Bold;
        titleTxt.color = new Color(0.95f, 0.90f, 0.80f);
        RectTransform tRt = titleObj.GetComponent<RectTransform>();
        tRt.anchorMin = new Vector2(0, 1);
        tRt.anchorMax = new Vector2(0.8f, 1);
        tRt.pivot = new Vector2(0, 1);
        tRt.offsetMin = new Vector2(24, -45);
        tRt.offsetMax = new Vector2(0, -15);

        // Badge
        GameObject badgeObj = CreateUIElement("Category_Badge", box.transform);
        Image badgeImg = badgeObj.AddComponent<Image>();
        badgeImg.color = new Color(0.2f, 0.45f, 0.7f);
        RectTransform bRt = badgeObj.GetComponent<RectTransform>();
        bRt.anchorMin = new Vector2(0, 1);
        bRt.anchorMax = new Vector2(0.45f, 1);
        bRt.pivot = new Vector2(0, 1);
        bRt.offsetMin = new Vector2(24, -75);
        bRt.offsetMax = new Vector2(0, -50);

        GameObject badgeTxtObj = CreateUIElement("Label", badgeObj.transform);
        Text badgeTxt = badgeTxtObj.AddComponent<Text>();
        badgeTxt.text = "EVIDENCE";
        badgeTxt.fontSize = 11;
        badgeTxt.fontStyle = FontStyle.Bold;
        badgeTxt.alignment = TextAnchor.MiddleCenter;
        badgeTxt.color = Color.white;
        StretchToParent(badgeTxtObj.GetComponent<RectTransform>());

        // Photo
        GameObject photoObj = CreateUIElement("Photo_RawImage", box.transform);
        RawImage photoImg = photoObj.AddComponent<RawImage>();
        photoImg.color = new Color(0.18f, 0.18f, 0.20f);
        RectTransform pRt = photoObj.GetComponent<RectTransform>();
        pRt.anchorMin = new Vector2(0, 0);
        pRt.anchorMax = new Vector2(0.44f, 1);
        pRt.offsetMin = new Vector2(24, 24);
        pRt.offsetMax = new Vector2(0, -90);

        // Details Text
        GameObject detailsObj = CreateUIElement("Details_Text", box.transform);
        Text detailsTxt = detailsObj.AddComponent<Text>();
        detailsTxt.text = "Thông tin chi tiết bằng chứng...";
        detailsTxt.fontSize = 13;
        detailsTxt.color = new Color(0.88f, 0.88f, 0.88f);
        RectTransform dRt = detailsObj.GetComponent<RectTransform>();
        dRt.anchorMin = new Vector2(0.47f, 0);
        dRt.anchorMax = new Vector2(1, 1);
        dRt.offsetMin = new Vector2(10, 24);
        dRt.offsetMax = new Vector2(-24, -90);

        // Close Button
        GameObject closeBtn = CreateButton("Btn_Close_X", box.transform, "X", new Color(0.7f, 0.15f, 0.15f));
        RectTransform cRt = closeBtn.GetComponent<RectTransform>();
        cRt.anchorMin = new Vector2(1, 1);
        cRt.anchorMax = new Vector2(1, 1);
        cRt.pivot = new Vector2(1, 1);
        cRt.sizeDelta = new Vector2(36, 32);
        cRt.anchoredPosition = new Vector2(-15, -15);

        EvidenceDetailModal modalComp = modal.GetComponent<EvidenceDetailModal>();
        if (modalComp == null) modalComp = modal.AddComponent<EvidenceDetailModal>();
        SerializedObject mSO = new SerializedObject(modalComp);
        mSO.FindProperty("modalRoot").objectReferenceValue = modal;
        mSO.FindProperty("titleText").objectReferenceValue = titleTxt;
        mSO.FindProperty("categoryBadgeText").objectReferenceValue = badgeTxt;
        mSO.FindProperty("badgeBackground").objectReferenceValue = badgeImg;
        mSO.FindProperty("photoImage").objectReferenceValue = photoImg;
        mSO.FindProperty("detailsText").objectReferenceValue = detailsTxt;
        mSO.FindProperty("closeButton").objectReferenceValue = closeBtn.GetComponent<Button>();
        mSO.ApplyModifiedProperties();

        modal.SetActive(false);
        return modal;
    }

    private static GameObject EnsureAccusationModal(Transform canvasTransform)
    {
        Transform existing = canvasTransform.Find("Accusation_Modal");
        if (existing == null) existing = canvasTransform.Find("Viewport_16_9_Room/Accusation_Modal");
        if (existing != null) DestroyImmediate(existing.gameObject);

        GameObject modal = CreateUIElement("Accusation_Modal", canvasTransform);
        StretchToParent(modal.GetComponent<RectTransform>());
        Image bg = modal.AddComponent<Image>();
        bg.color = Color.clear;
        bg.raycastTarget = false;

        GameObject box = CreateUIElement("Accusation_Box", modal.transform);
        Image boxImg = box.AddComponent<Image>();
        boxImg.color = new Color(0.12f, 0.10f, 0.09f);
        RectTransform boxRt = box.GetComponent<RectTransform>();
        boxRt.sizeDelta = new Vector2(680, 540);
        boxRt.anchoredPosition = Vector2.zero;

        // Title
        GameObject titleObj = CreateUIElement("Title_Text", box.transform);
        Text titleTxt = titleObj.AddComponent<Text>();
        titleTxt.text = "CHỈ ĐỊNH THỦ PHẠM & BẰNG CHỨNG";
        titleTxt.fontSize = 20;
        titleTxt.fontStyle = FontStyle.Bold;
        titleTxt.color = new Color(0.92f, 0.86f, 0.74f);
        RectTransform tRt = titleObj.GetComponent<RectTransform>();
        tRt.anchorMin = new Vector2(0, 1);
        tRt.anchorMax = new Vector2(1, 1);
        tRt.pivot = new Vector2(0.5f, 1);
        tRt.sizeDelta = new Vector2(0, 40);
        tRt.anchoredPosition = new Vector2(0, -15);
        titleTxt.alignment = TextAnchor.MiddleCenter;

        // Suspect Dropdown
        GameObject ddObj = CreateUIElement("Suspect_Dropdown", box.transform);
        Image ddImg = ddObj.AddComponent<Image>();
        ddImg.color = new Color(0.18f, 0.18f, 0.20f);
        Dropdown dd = ddObj.AddComponent<Dropdown>();
        RectTransform ddRt = ddObj.GetComponent<RectTransform>();
        ddRt.anchorMin = new Vector2(0.08f, 0.78f);
        ddRt.anchorMax = new Vector2(0.92f, 0.87f);
        ddRt.offsetMin = Vector2.zero;
        ddRt.offsetMax = Vector2.zero;

        GameObject ddLabel = CreateUIElement("Label", ddObj.transform);
        Text ddLabelTxt = ddLabel.AddComponent<Text>();
        ddLabelTxt.text = "Chọn thủ phạm...";
        ddLabelTxt.fontSize = 14;
        ddLabelTxt.color = Color.white;
        ddLabelTxt.alignment = TextAnchor.MiddleLeft;
        StretchToParent(ddLabel.GetComponent<RectTransform>());
        ddLabel.GetComponent<RectTransform>().offsetMin = new Vector2(12, 0);
        dd.captionText = ddLabelTxt;

        // Evidence Toggles Container
        GameObject containerObj = CreateUIElement("Evidence_Container", box.transform);
        RectTransform cRt = containerObj.GetComponent<RectTransform>();
        cRt.anchorMin = new Vector2(0.08f, 0.22f);
        cRt.anchorMax = new Vector2(0.92f, 0.75f);
        cRt.offsetMin = Vector2.zero;
        cRt.offsetMax = Vector2.zero;
        VerticalLayoutGroup vlg = containerObj.AddComponent<VerticalLayoutGroup>();
        vlg.spacing = 6;
        vlg.childForceExpandHeight = false;

        // Evidence Toggle Prefab
        GameObject togglePrefab = CreateUIElement("Toggle_Prefab", box.transform);
        Toggle tog = togglePrefab.AddComponent<Toggle>();
        RectTransform togRt = togglePrefab.GetComponent<RectTransform>();
        togRt.sizeDelta = new Vector2(580, 28);
        Image togBg = togglePrefab.AddComponent<Image>();
        togBg.color = new Color(0.16f, 0.16f, 0.18f);

        GameObject togCheck = CreateUIElement("Checkmark", togglePrefab.transform);
        Image checkImg = togCheck.AddComponent<Image>();
        checkImg.color = new Color(0.85f, 0.25f, 0.25f);
        RectTransform ckRt = togCheck.GetComponent<RectTransform>();
        ckRt.anchorMin = new Vector2(0, 0.5f);
        ckRt.anchorMax = new Vector2(0, 0.5f);
        ckRt.sizeDelta = new Vector2(18, 18);
        ckRt.anchoredPosition = new Vector2(14, 0);
        tog.graphic = checkImg;

        GameObject togLabel = CreateUIElement("Label", togglePrefab.transform);
        Text togTxt = togLabel.AddComponent<Text>();
        togTxt.text = "Chứng cứ mâu thuẫn";
        togTxt.fontSize = 13;
        togTxt.color = Color.white;
        togTxt.alignment = TextAnchor.MiddleLeft;
        RectTransform tlRt = togLabel.GetComponent<RectTransform>();
        tlRt.anchorMin = new Vector2(0, 0);
        tlRt.anchorMax = new Vector2(1, 1);
        tlRt.offsetMin = new Vector2(32, 0);
        tlRt.offsetMax = Vector2.zero;
        togglePrefab.SetActive(false);

        // Submit Button
        GameObject submitBtn = CreateButton("Btn_Submit", box.transform, "GỬI KẾT TỘI", new Color(0.75f, 0.15f, 0.15f));
        RectTransform sRt = submitBtn.GetComponent<RectTransform>();
        sRt.anchorMin = new Vector2(0.52f, 0.05f);
        sRt.anchorMax = new Vector2(0.92f, 0.17f);
        sRt.offsetMin = Vector2.zero;
        sRt.offsetMax = Vector2.zero;

        // Cancel Button
        GameObject cancelBtn = CreateButton("Btn_Cancel", box.transform, "HỦY BỎ", new Color(0.3f, 0.3f, 0.32f));
        RectTransform cnRt = cancelBtn.GetComponent<RectTransform>();
        cnRt.anchorMin = new Vector2(0.08f, 0.05f);
        cnRt.anchorMax = new Vector2(0.48f, 0.17f);
        cnRt.offsetMin = Vector2.zero;
        cnRt.offsetMax = Vector2.zero;

        // Verdict Panel
        GameObject vPanel = CreateUIElement("Verdict_Panel", modal.transform);
        StretchToParent(vPanel.GetComponent<RectTransform>());
        Image vBg = vPanel.AddComponent<Image>();
        vBg.color = new Color(0, 0, 0, 0.90f);

        GameObject vBox = CreateUIElement("Verdict_Box", vPanel.transform);
        Image vbImg = vBox.AddComponent<Image>();
        vbImg.color = new Color(0.12f, 0.11f, 0.10f);
        RectTransform vbRt = vBox.GetComponent<RectTransform>();
        vbRt.sizeDelta = new Vector2(600, 380);
        vbRt.anchoredPosition = Vector2.zero;

        GameObject vTitle = CreateUIElement("Verdict_Title", vBox.transform);
        Text vtTxt = vTitle.AddComponent<Text>();
        vtTxt.text = "KẾT QUẢ KẾT TỘI";
        vtTxt.fontSize = 22;
        vtTxt.fontStyle = FontStyle.Bold;
        vtTxt.alignment = TextAnchor.MiddleCenter;
        vtTxt.color = Color.white;
        RectTransform vtRt = vTitle.GetComponent<RectTransform>();
        vtRt.anchorMin = new Vector2(0, 1);
        vtRt.anchorMax = new Vector2(1, 1);
        vtRt.pivot = new Vector2(0.5f, 1);
        vtRt.sizeDelta = new Vector2(0, 45);
        vtRt.anchoredPosition = new Vector2(0, -15);

        GameObject vFb = CreateUIElement("Verdict_Feedback", vBox.transform);
        Text vfbTxt = vFb.AddComponent<Text>();
        vfbTxt.text = "Phản hồi từ AI Validator...";
        vfbTxt.fontSize = 14;
        vfbTxt.color = new Color(0.9f, 0.9f, 0.9f);
        RectTransform vfbRt = vFb.GetComponent<RectTransform>();
        vfbRt.anchorMin = new Vector2(0.08f, 0.45f);
        vfbRt.anchorMax = new Vector2(0.92f, 0.82f);
        vfbRt.offsetMin = Vector2.zero;
        vfbRt.offsetMax = Vector2.zero;

        GameObject vContra = CreateUIElement("Core_Contradiction", vBox.transform);
        Text vcTxt = vContra.AddComponent<Text>();
        vcTxt.text = "Mâu thuẫn then chốt...";
        vcTxt.fontSize = 13;
        vcTxt.fontStyle = FontStyle.Italic;
        vcTxt.color = new Color(0.85f, 0.75f, 0.4f);
        RectTransform vcRt = vContra.GetComponent<RectTransform>();
        vcRt.anchorMin = new Vector2(0.08f, 0.22f);
        vcRt.anchorMax = new Vector2(0.92f, 0.42f);
        vcRt.offsetMin = Vector2.zero;
        vcRt.offsetMax = Vector2.zero;

        GameObject vCloseBtn = CreateButton("Btn_Close_Verdict", vBox.transform, "XÁC NHẬN", new Color(0.2f, 0.45f, 0.3f));
        RectTransform vcbRt = vCloseBtn.GetComponent<RectTransform>();
        vcbRt.anchorMin = new Vector2(0.35f, 0.06f);
        vcbRt.anchorMax = new Vector2(0.65f, 0.18f);
        vcbRt.offsetMin = Vector2.zero;
        vcbRt.offsetMax = Vector2.zero;

        vPanel.SetActive(false);

        // Wire AccusationModal
        AccusationModal modalComp = modal.GetComponent<AccusationModal>();
        if (modalComp == null) modalComp = modal.AddComponent<AccusationModal>();
        SerializedObject aSO = new SerializedObject(modalComp);
        aSO.FindProperty("modalRoot").objectReferenceValue = modal;
        aSO.FindProperty("suspectDropdown").objectReferenceValue = dd;
        aSO.FindProperty("evidenceTogglesContainer").objectReferenceValue = containerObj.transform;
        aSO.FindProperty("evidenceTogglePrefab").objectReferenceValue = togglePrefab;
        aSO.FindProperty("submitButton").objectReferenceValue = submitBtn.GetComponent<Button>();
        aSO.FindProperty("closeButton").objectReferenceValue = cancelBtn.GetComponent<Button>();
        aSO.FindProperty("verdictPanel").objectReferenceValue = vPanel;
        aSO.FindProperty("verdictTitleText").objectReferenceValue = vtTxt;
        aSO.FindProperty("verdictFeedbackText").objectReferenceValue = vfbTxt;
        aSO.FindProperty("coreContradictionText").objectReferenceValue = vcTxt;
        aSO.FindProperty("closeVerdictButton").objectReferenceValue = vCloseBtn.GetComponent<Button>();
        aSO.ApplyModifiedProperties();

        modal.SetActive(false);
        return modal;
    }

    private static GameObject EnsureAutopsyReportModal(Transform canvasTransform)
    {
        Transform existing = canvasTransform.Find("Autopsy_Report_Modal");
        if (existing == null) existing = canvasTransform.Find("Viewport_16_9_Room/Autopsy_Report_Modal");
        if (existing != null) DestroyImmediate(existing.gameObject);

        GameObject modal = CreateUIElement("Autopsy_Report_Modal", canvasTransform);
        StretchToParent(modal.GetComponent<RectTransform>());
        Image bg = modal.AddComponent<Image>();
        bg.color = Color.clear;
        bg.raycastTarget = false;

        GameObject box = CreateUIElement("Autopsy_Box", modal.transform);
        Image boxImg = box.AddComponent<Image>();
        boxImg.color = new Color(0.11f, 0.10f, 0.09f); // Noir forensic folder tone
        RectTransform boxRt = box.GetComponent<RectTransform>();
        boxRt.sizeDelta = new Vector2(740, 560);
        boxRt.anchoredPosition = Vector2.zero;

        // Header Title Bar
        GameObject headerBar = CreateUIElement("Header_Bar", box.transform);
        Image hbImg = headerBar.AddComponent<Image>();
        hbImg.color = new Color(0.48f, 0.12f, 0.12f);
        RectTransform hbRt = headerBar.GetComponent<RectTransform>();
        hbRt.anchorMin = new Vector2(0, 1);
        hbRt.anchorMax = new Vector2(1, 1);
        hbRt.pivot = new Vector2(0.5f, 1);
        hbRt.sizeDelta = new Vector2(0, 42);
        hbRt.anchoredPosition = Vector2.zero;

        GameObject titleObj = CreateUIElement("Header_Title", headerBar.transform);
        Text titleTxt = titleObj.AddComponent<Text>();
        titleTxt.text = "HỘI ĐỒNG GIÁM ĐỊNH PHÁP Y // CORONER'S AUTOPSY REPORT";
        titleTxt.fontSize = 14;
        titleTxt.fontStyle = FontStyle.Bold;
        titleTxt.alignment = TextAnchor.MiddleCenter;
        titleTxt.color = new Color(0.96f, 0.94f, 0.88f);
        StretchToParent(titleObj.GetComponent<RectTransform>());

        // Victim Name
        GameObject vNameObj = CreateUIElement("Victim_Name", box.transform);
        Text vnTxt = vNameObj.AddComponent<Text>();
        vnTxt.text = "NẠN NHÂN: LORD ARCHIBALD BLACKWOOD";
        vnTxt.fontSize = 18;
        vnTxt.fontStyle = FontStyle.Bold;
        vnTxt.color = new Color(0.95f, 0.88f, 0.72f);
        RectTransform vnRt = vNameObj.GetComponent<RectTransform>();
        vnRt.anchorMin = new Vector2(0.06f, 0.85f);
        vnRt.anchorMax = new Vector2(0.94f, 0.92f);
        vnRt.offsetMin = Vector2.zero;
        vnRt.offsetMax = Vector2.zero;

        // Victim Metadata
        GameObject vMetaObj = CreateUIElement("Victim_Meta", box.transform);
        Text vmTxt = vMetaObj.AddComponent<Text>();
        vmTxt.text = "<b>Tuổi:</b> 62  |  <b>Nghề nghiệp:</b> Quý tộc  |  <b>Hồ sơ vụ án:</b> #2026-001";
        vmTxt.fontSize = 12;
        vmTxt.color = new Color(0.78f, 0.75f, 0.70f);
        RectTransform vmRt = vMetaObj.GetComponent<RectTransform>();
        vmRt.anchorMin = new Vector2(0.06f, 0.80f);
        vmRt.anchorMax = new Vector2(0.94f, 0.85f);
        vmRt.offsetMin = Vector2.zero;
        vmRt.offsetMax = Vector2.zero;

        // Panel Left: Henssge Thermodynamic Temperature Data
        GameObject pLeft = CreateUIElement("Panel_Left_Thermodynamics", box.transform);
        Image plImg = pLeft.AddComponent<Image>();
        plImg.color = new Color(0.07f, 0.08f, 0.09f);
        RectTransform plRt = pLeft.GetComponent<RectTransform>();
        plRt.anchorMin = new Vector2(0.06f, 0.18f);
        plRt.anchorMax = new Vector2(0.48f, 0.78f);
        plRt.offsetMin = Vector2.zero;
        plRt.offsetMax = Vector2.zero;

        GameObject plTitle = CreateUIElement("Title", pLeft.transform);
        Text pltTxt = plTitle.AddComponent<Text>();
        pltTxt.text = "PHÂN TÍCH NHIỆT HỌC HENSSGE\n<size=10>(TWO-EXPONENTIAL COOLING)</size>";
        pltTxt.fontSize = 11;
        pltTxt.fontStyle = FontStyle.Bold;
        pltTxt.alignment = TextAnchor.MiddleCenter;
        pltTxt.color = new Color(0.42f, 0.82f, 0.95f);
        RectTransform pltRt = plTitle.GetComponent<RectTransform>();
        pltRt.anchorMin = new Vector2(0, 0.82f);
        pltRt.anchorMax = new Vector2(1, 1);
        pltRt.offsetMin = Vector2.zero;
        pltRt.offsetMax = Vector2.zero;

        // Body Temp
        GameObject btLabel = CreateUIElement("Body_Temp_Label", pLeft.transform);
        Text btlTxt = btLabel.AddComponent<Text>();
        btlTxt.text = "Thân nhiệt trực tràng (T_body):";
        btlTxt.fontSize = 11;
        btlTxt.color = new Color(0.7f, 0.7f, 0.7f);
        RectTransform btlRt = btLabel.GetComponent<RectTransform>();
        btlRt.anchorMin = new Vector2(0.08f, 0.65f);
        btlRt.anchorMax = new Vector2(0.92f, 0.78f);
        btlRt.offsetMin = Vector2.zero;
        btlRt.offsetMax = Vector2.zero;

        GameObject btVal = CreateUIElement("Body_Temp_Value", pLeft.transform);
        Text btvTxt = btVal.AddComponent<Text>();
        btvTxt.text = "31.2 °C";
        btvTxt.fontSize = 18;
        btvTxt.fontStyle = FontStyle.Bold;
        btvTxt.color = new Color(0.95f, 0.45f, 0.45f);
        RectTransform btvRt = btVal.GetComponent<RectTransform>();
        btvRt.anchorMin = new Vector2(0.08f, 0.52f);
        btvRt.anchorMax = new Vector2(0.92f, 0.65f);
        btvRt.offsetMin = Vector2.zero;
        btvRt.offsetMax = Vector2.zero;

        // Ambient Temp
        GameObject atLabel = CreateUIElement("Ambient_Temp_Label", pLeft.transform);
        Text atlTxt = atLabel.AddComponent<Text>();
        atlTxt.text = "Nhiệt độ phòng (T_ambient):";
        atlTxt.fontSize = 11;
        atlTxt.color = new Color(0.7f, 0.7f, 0.7f);
        RectTransform atlRt = atLabel.GetComponent<RectTransform>();
        atlRt.anchorMin = new Vector2(0.08f, 0.38f);
        atlRt.anchorMax = new Vector2(0.92f, 0.50f);
        atlRt.offsetMin = Vector2.zero;
        atlRt.offsetMax = Vector2.zero;

        GameObject atVal = CreateUIElement("Ambient_Temp_Value", pLeft.transform);
        Text atvTxt = atVal.AddComponent<Text>();
        atvTxt.text = "18.5 °C";
        atvTxt.fontSize = 18;
        atvTxt.fontStyle = FontStyle.Bold;
        atvTxt.color = new Color(0.45f, 0.85f, 0.95f);
        RectTransform atvRt = atVal.GetComponent<RectTransform>();
        atvRt.anchorMin = new Vector2(0.08f, 0.25f);
        atvRt.anchorMax = new Vector2(0.92f, 0.38f);
        atvRt.offsetMin = Vector2.zero;
        atvRt.offsetMax = Vector2.zero;

        // Formula Note
        GameObject formulaObj = CreateUIElement("Formula_Note", pLeft.transform);
        Text fTxt = formulaObj.AddComponent<Text>();
        fTxt.text = "<size=9><i>(T - Ta)/(37.2 - Ta) = 1.25e^(-kt) - 0.25e^(-5kt)\nChu kỳ làm lạnh nhiệt học cơ thể</i></size>";
        fTxt.fontSize = 10;
        fTxt.color = new Color(0.6f, 0.6f, 0.65f);
        fTxt.alignment = TextAnchor.MiddleCenter;
        RectTransform fRt = formulaObj.GetComponent<RectTransform>();
        fRt.anchorMin = new Vector2(0.05f, 0.02f);
        fRt.anchorMax = new Vector2(0.95f, 0.24f);
        fRt.offsetMin = Vector2.zero;
        fRt.offsetMax = Vector2.zero;

        // Panel Right: Medical Examiner Findings
        GameObject pRight = CreateUIElement("Panel_Right_Findings", box.transform);
        Image prImg = pRight.AddComponent<Image>();
        prImg.color = new Color(0.07f, 0.08f, 0.09f);
        RectTransform prRt = pRight.GetComponent<RectTransform>();
        prRt.anchorMin = new Vector2(0.52f, 0.18f);
        prRt.anchorMax = new Vector2(0.94f, 0.78f);
        prRt.offsetMin = Vector2.zero;
        prRt.offsetMax = Vector2.zero;

        GameObject prTitle = CreateUIElement("Title", pRight.transform);
        Text prtTxt = prTitle.AddComponent<Text>();
        prtTxt.text = "KẾT LUẬN Y KHOA PHÁP CHỨNG\n<size=10>(FORENSIC PATHOLOGY)</size>";
        prtTxt.fontSize = 11;
        prtTxt.fontStyle = FontStyle.Bold;
        prtTxt.alignment = TextAnchor.MiddleCenter;
        prtTxt.color = new Color(0.95f, 0.85f, 0.42f);
        RectTransform prtRt = prTitle.GetComponent<RectTransform>();
        prtRt.anchorMin = new Vector2(0, 0.82f);
        prtRt.anchorMax = new Vector2(1, 1);
        prtRt.offsetMin = Vector2.zero;
        prtRt.offsetMax = Vector2.zero;

        // TOD Window
        GameObject todLabel = CreateUIElement("TOD_Label", pRight.transform);
        Text todlTxt = todLabel.AddComponent<Text>();
        todlTxt.text = "Khung giờ tử vong ước tính (TOD Window):";
        todlTxt.fontSize = 11;
        todlTxt.color = new Color(0.7f, 0.7f, 0.7f);
        RectTransform todlRt = todLabel.GetComponent<RectTransform>();
        todlRt.anchorMin = new Vector2(0.08f, 0.65f);
        todlRt.anchorMax = new Vector2(0.92f, 0.78f);
        todlRt.offsetMin = Vector2.zero;
        todlRt.offsetMax = Vector2.zero;

        GameObject todVal = CreateUIElement("TOD_Value", pRight.transform);
        Text todvTxt = todVal.AddComponent<Text>();
        todvTxt.text = "[21:15 - 22:45]";
        todvTxt.fontSize = 18;
        todvTxt.fontStyle = FontStyle.Bold;
        todvTxt.color = new Color(0.95f, 0.82f, 0.35f);
        RectTransform todvRt = todVal.GetComponent<RectTransform>();
        todvRt.anchorMin = new Vector2(0.08f, 0.52f);
        todvRt.anchorMax = new Vector2(0.92f, 0.65f);
        todvRt.offsetMin = Vector2.zero;
        todvRt.offsetMax = Vector2.zero;

        // Livor Mortis
        GameObject livorLabel = CreateUIElement("Livor_Label", pRight.transform);
        Text livlTxt = livorLabel.AddComponent<Text>();
        livlTxt.text = "Hoen tử thi (Livor Mortis):";
        livlTxt.fontSize = 11;
        livlTxt.color = new Color(0.7f, 0.7f, 0.7f);
        RectTransform livlRt = livorLabel.GetComponent<RectTransform>();
        livlRt.anchorMin = new Vector2(0.08f, 0.38f);
        livlRt.anchorMax = new Vector2(0.92f, 0.50f);
        livlRt.offsetMin = Vector2.zero;
        livlRt.offsetMax = Vector2.zero;

        GameObject livorVal = CreateUIElement("Livor_Value", pRight.transform);
        Text livvTxt = livorVal.AddComponent<Text>();
        livvTxt.text = "Hoen tử thi cố định mặt sau, không đổi màu khi ấn";
        livvTxt.fontSize = 11;
        livvTxt.fontStyle = FontStyle.Italic;
        livvTxt.color = new Color(0.92f, 0.90f, 0.88f);
        RectTransform livvRt = livorVal.GetComponent<RectTransform>();
        livvRt.anchorMin = new Vector2(0.08f, 0.28f);
        livvRt.anchorMax = new Vector2(0.92f, 0.39f);
        livvRt.offsetMin = Vector2.zero;
        livvRt.offsetMax = Vector2.zero;

        // Fatal Wound
        GameObject woundLabel = CreateUIElement("Wound_Label", pRight.transform);
        Text wndlTxt = woundLabel.AddComponent<Text>();
        wndlTxt.text = "Vết thương chí mạng (Cause of Death):";
        wndlTxt.fontSize = 11;
        wndlTxt.color = new Color(0.7f, 0.7f, 0.7f);
        RectTransform wndlRt = woundLabel.GetComponent<RectTransform>();
        wndlRt.anchorMin = new Vector2(0.08f, 0.16f);
        wndlRt.anchorMax = new Vector2(0.92f, 0.28f);
        wndlRt.offsetMin = Vector2.zero;
        wndlRt.offsetMax = Vector2.zero;

        GameObject woundVal = CreateUIElement("Wound_Value", pRight.transform);
        Text wndvTxt = woundVal.AddComponent<Text>();
        wndvTxt.text = "Vết thương hở do vật sắc nhọn gây mất máu cấp";
        wndvTxt.fontSize = 11;
        wndvTxt.fontStyle = FontStyle.Italic;
        wndvTxt.color = new Color(0.92f, 0.90f, 0.88f);
        RectTransform wndvRt = woundVal.GetComponent<RectTransform>();
        wndvRt.anchorMin = new Vector2(0.08f, 0.04f);
        wndvRt.anchorMax = new Vector2(0.92f, 0.16f);
        wndvRt.offsetMin = Vector2.zero;
        wndvRt.offsetMax = Vector2.zero;

        // Close Button
        GameObject closeBtn = CreateButton("Btn_Close_Autopsy", box.transform, "ĐÓNG HỒ SƠ [X]", new Color(0.65f, 0.18f, 0.18f));
        RectTransform cbRt = closeBtn.GetComponent<RectTransform>();
        cbRt.anchorMin = new Vector2(0.35f, 0.03f);
        cbRt.anchorMax = new Vector2(0.65f, 0.13f);
        cbRt.offsetMin = Vector2.zero;
        cbRt.offsetMax = Vector2.zero;

        // Wire AutopsyReportModal component
        AutopsyReportModal comp = modal.GetComponent<AutopsyReportModal>();
        if (comp == null) comp = modal.AddComponent<AutopsyReportModal>();
        SerializedObject so = new SerializedObject(comp);
        so.FindProperty("modalRoot").objectReferenceValue = modal;
        so.FindProperty("victimNameText").objectReferenceValue = vnTxt;
        so.FindProperty("victimMetaText").objectReferenceValue = vmTxt;
        so.FindProperty("bodyTempText").objectReferenceValue = btvTxt;
        so.FindProperty("ambientTempText").objectReferenceValue = atvTxt;
        so.FindProperty("estimatedTodText").objectReferenceValue = todvTxt;
        so.FindProperty("livorMortisText").objectReferenceValue = livvTxt;
        so.FindProperty("woundText").objectReferenceValue = wndvTxt;
        so.FindProperty("closeButton").objectReferenceValue = closeBtn.GetComponent<Button>();
        so.ApplyModifiedProperties();

        modal.SetActive(false);
        return modal;
    }

    private static GameObject EnsureGenerateCaseModal(Transform canvasTransform)
    {
        Transform existing = canvasTransform.Find("Generate_Case_Modal");
        if (existing == null) existing = canvasTransform.Find("Viewport_16_9_Room/Generate_Case_Modal");
        if (existing != null) DestroyImmediate(existing.gameObject);

        GameObject modal = CreateUIElement("Generate_Case_Modal", canvasTransform);
        StretchToParent(modal.GetComponent<RectTransform>());
        Image bg = modal.AddComponent<Image>();
        bg.color = Color.clear;
        bg.raycastTarget = false;

        GameObject box = CreateUIElement("Generator_Box", modal.transform);
        Image boxImg = box.AddComponent<Image>();
        boxImg.color = new Color(0.10f, 0.11f, 0.13f);
        RectTransform boxRt = box.GetComponent<RectTransform>();
        boxRt.sizeDelta = new Vector2(700, 520);
        boxRt.anchoredPosition = Vector2.zero;

        // Header Title
        GameObject headerBar = CreateUIElement("Header_Bar", box.transform);
        Image hbImg = headerBar.AddComponent<Image>();
        hbImg.color = new Color(0.12f, 0.38f, 0.28f);
        RectTransform hbRt = headerBar.GetComponent<RectTransform>();
        hbRt.anchorMin = new Vector2(0, 1);
        hbRt.anchorMax = new Vector2(1, 1);
        hbRt.pivot = new Vector2(0.5f, 1);
        hbRt.sizeDelta = new Vector2(0, 42);
        hbRt.anchoredPosition = Vector2.zero;

        GameObject titleObj = CreateUIElement("Header_Title", headerBar.transform);
        Text titleTxt = titleObj.AddComponent<Text>();
        titleTxt.text = "HỆ THỐNG ĐIỀU TRA TỰ ĐỘNG // TẠO VỤ ÁN MỚI (AI CASE GENERATOR)";
        titleTxt.fontSize = 13;
        titleTxt.fontStyle = FontStyle.Bold;
        titleTxt.alignment = TextAnchor.MiddleCenter;
        titleTxt.color = new Color(0.95f, 0.98f, 0.95f);
        StretchToParent(titleObj.GetComponent<RectTransform>());

        // Subheader Description
        GameObject subObj = CreateUIElement("Subheader", box.transform);
        Text subTxt = subObj.AddComponent<Text>();
        subTxt.text = "Nhập bối cảnh hoặc chọn kịch bản mẫu để kích hoạt quy trình 4 Tác tử (Multi-Agent Pipeline):\n<b>OutlineAgent</b> ➔ <b>CharacterAgent</b> ➔ <b>ClueAgent (Henssge)</b> ➔ <b>DeductionAgent (Solvability)</b>";
        subTxt.fontSize = 11;
        subTxt.color = new Color(0.78f, 0.82f, 0.85f);
        subTxt.alignment = TextAnchor.MiddleLeft;
        RectTransform subRt = subObj.GetComponent<RectTransform>();
        subRt.anchorMin = new Vector2(0.08f, 0.77f);
        subRt.anchorMax = new Vector2(0.92f, 0.88f);
        subRt.offsetMin = Vector2.zero;
        subRt.offsetMax = Vector2.zero;

        // Theme Input Field
        GameObject inputObj = CreateInputField("Theme_InputField", box.transform, "Nhập chủ đề vụ án (ví dụ: Án mạng trong bảo tàng cổ vật...)");
        RectTransform inRt = inputObj.GetComponent<RectTransform>();
        inRt.anchorMin = new Vector2(0.08f, 0.65f);
        inRt.anchorMax = new Vector2(0.92f, 0.75f);
        inRt.offsetMin = Vector2.zero;
        inRt.offsetMax = Vector2.zero;

        // Preset Label
        GameObject pLabelObj = CreateUIElement("Presets_Label", box.transform);
        Text plTxt = pLabelObj.AddComponent<Text>();
        plTxt.text = "KỊCH BẢN MẪU (PRESET SCENARIOS):";
        plTxt.fontSize = 11;
        plTxt.fontStyle = FontStyle.Bold;
        plTxt.color = new Color(0.85f, 0.75f, 0.45f);
        RectTransform plRt = pLabelObj.GetComponent<RectTransform>();
        plRt.anchorMin = new Vector2(0.08f, 0.57f);
        plRt.anchorMax = new Vector2(0.92f, 0.63f);
        plRt.offsetMin = Vector2.zero;
        plRt.offsetMax = Vector2.zero;

        // 3 Preset Buttons
        GameObject p1Btn = CreateButton("Btn_Preset_1", box.transform, "[1] Bí ẩn Biệt thự cổ Blackwood", new Color(0.18f, 0.22f, 0.26f));
        RectTransform p1Rt = p1Btn.GetComponent<RectTransform>();
        p1Rt.anchorMin = new Vector2(0.08f, 0.46f);
        p1Rt.anchorMax = new Vector2(0.92f, 0.55f);
        p1Rt.offsetMin = Vector2.zero;
        p1Rt.offsetMax = Vector2.zero;

        GameObject p2Btn = CreateButton("Btn_Preset_2", box.transform, "[2] Bí mật phòng thí nghiệm Trí tuệ Nhân tạo", new Color(0.18f, 0.22f, 0.26f));
        RectTransform p2Rt = p2Btn.GetComponent<RectTransform>();
        p2Rt.anchorMin = new Vector2(0.08f, 0.35f);
        p2Rt.anchorMax = new Vector2(0.92f, 0.44f);
        p2Rt.offsetMin = Vector2.zero;
        p2Rt.offsetMax = Vector2.zero;

        GameObject p3Btn = CreateButton("Btn_Preset_3", box.transform, "[3] Án mạng trên Chuyến tàu Đêm Hà Nội - Sài Gòn", new Color(0.18f, 0.22f, 0.26f));
        RectTransform p3Rt = p3Btn.GetComponent<RectTransform>();
        p3Rt.anchorMin = new Vector2(0.08f, 0.24f);
        p3Rt.anchorMax = new Vector2(0.92f, 0.33f);
        p3Rt.offsetMin = Vector2.zero;
        p3Rt.offsetMax = Vector2.zero;

        // Action Buttons: Cancel & Generate
        GameObject cancelBtn = CreateButton("Btn_Cancel", box.transform, "HỦY BỎ", new Color(0.32f, 0.32f, 0.35f));
        RectTransform cnRt = cancelBtn.GetComponent<RectTransform>();
        cnRt.anchorMin = new Vector2(0.08f, 0.08f);
        cnRt.anchorMax = new Vector2(0.42f, 0.19f);
        cnRt.offsetMin = Vector2.zero;
        cnRt.offsetMax = Vector2.zero;

        GameObject genBtn = CreateButton("Btn_Generate", box.transform, "KÍCH HOẠT QUY TRÌNH MULTI-AGENT", new Color(0.14f, 0.55f, 0.32f));
        RectTransform gnRt = genBtn.GetComponent<RectTransform>();
        gnRt.anchorMin = new Vector2(0.45f, 0.08f);
        gnRt.anchorMax = new Vector2(0.92f, 0.19f);
        gnRt.offsetMin = Vector2.zero;
        gnRt.offsetMax = Vector2.zero;

        // Loading Overlay Panel
        GameObject loadPanel = CreateUIElement("Loading_Panel", box.transform);
        Image lpImg = loadPanel.AddComponent<Image>();
        lpImg.color = new Color(0.06f, 0.07f, 0.08f, 0.96f);
        StretchToParent(loadPanel.GetComponent<RectTransform>());

        GameObject loadStatus = CreateUIElement("Status_Text", loadPanel.transform);
        Text lsTxt = loadStatus.AddComponent<Text>();
        lsTxt.text = "Khởi động Multi-Agent Pipeline... [Tác tử 1/4: OutlineAgent]";
        lsTxt.fontSize = 14;
        lsTxt.fontStyle = FontStyle.Bold;
        lsTxt.alignment = TextAnchor.MiddleCenter;
        lsTxt.color = new Color(0.38f, 0.88f, 0.55f);
        StretchToParent(loadStatus.GetComponent<RectTransform>());
        loadStatus.GetComponent<RectTransform>().offsetMin = new Vector2(40, 40);
        loadStatus.GetComponent<RectTransform>().offsetMax = new Vector2(-40, -40);

        loadPanel.SetActive(false);

        // Wire GenerateCaseModal
        GenerateCaseModal comp = modal.GetComponent<GenerateCaseModal>();
        if (comp == null) comp = modal.AddComponent<GenerateCaseModal>();
        SerializedObject so = new SerializedObject(comp);
        so.FindProperty("modalRoot").objectReferenceValue = modal;
        so.FindProperty("themeInputField").objectReferenceValue = inputObj.GetComponent<InputField>();
        so.FindProperty("generateButton").objectReferenceValue = genBtn.GetComponent<Button>();
        so.FindProperty("closeButton").objectReferenceValue = cancelBtn.GetComponent<Button>();
        so.FindProperty("preset1Button").objectReferenceValue = p1Btn.GetComponent<Button>();
        so.FindProperty("preset2Button").objectReferenceValue = p2Btn.GetComponent<Button>();
        so.FindProperty("preset3Button").objectReferenceValue = p3Btn.GetComponent<Button>();
        so.FindProperty("loadingPanel").objectReferenceValue = loadPanel;
        so.FindProperty("loadingStatusText").objectReferenceValue = lsTxt;
        so.ApplyModifiedProperties();

        modal.SetActive(false);
        return modal;
    }

    private static void BuildHotkeyTaskbar(Transform parent, Transform header, Font font, DetectiveChatUI chatUI)
    {
        GameObject bar = CreateUIElement("Hotkey_Taskbar", parent);
        RectTransform barRt = bar.GetComponent<RectTransform>();
        barRt.anchorMin = new Vector2(0, 0);
        barRt.anchorMax = new Vector2(1, 0);
        barRt.pivot = new Vector2(0.5f, 0);
        barRt.sizeDelta = new Vector2(0, 36);
        barRt.anchoredPosition = Vector2.zero;
        bar.AddComponent<Image>().color = new Color(0.04f, 0.04f, 0.05f, 0.9f);
        bar.transform.SetSiblingIndex(header.GetSiblingIndex() + 1);

        GameObject hints = CreateUIElement("Hints", bar.transform);
        RectTransform hintsRt = hints.GetComponent<RectTransform>();
        hintsRt.anchorMin = Vector2.zero;
        hintsRt.anchorMax = new Vector2(0.7f, 1);
        hintsRt.offsetMin = Vector2.zero;
        hintsRt.offsetMax = Vector2.zero;
        HorizontalLayoutGroup hl = hints.AddComponent<HorizontalLayoutGroup>();
        hl.padding = new RectOffset(10, 10, 5, 5);
        hl.spacing = 8;
        hl.childControlWidth = true;
        hl.childControlHeight = true;
        hl.childForceExpandWidth = false;
        hl.childForceExpandHeight = true;

        CreateHotkeyChip(hints.transform, "giữ V", "Nói (voice)", 150, font, false);
        GameObject chatChip = CreateHotkeyChip(hints.transform, "T", "Chat", 100, font, true);
        GameObject lobbyChip = CreateHotkeyChip(hints.transform, "L", "Phòng LAN", 140, font, true);
        CreateHotkeyChip(hints.transform, "Esc", "Đóng", 100, font, false);

        GameObject statusObj = CreateUIElement("Status", bar.transform);
        Text status = statusObj.AddComponent<Text>();
        status.font = font;
        status.text = "○ CHƠI ĐƠN";
        status.fontSize = 14;
        status.color = new Color(0.88f, 0.85f, 0.78f);
        status.alignment = TextAnchor.MiddleRight;
        status.raycastTarget = false;
        RectTransform stRt = statusObj.GetComponent<RectTransform>();
        stRt.anchorMin = new Vector2(0.7f, 0);
        stRt.anchorMax = Vector2.one;
        stRt.offsetMin = Vector2.zero;
        stRt.offsetMax = new Vector2(-16, 0);

        HotkeyTaskbar taskbar = bar.AddComponent<HotkeyTaskbar>();
        SerializedObject tso = new SerializedObject(taskbar);
        tso.FindProperty("statusText").objectReferenceValue = status;
        tso.FindProperty("chatChipButton").objectReferenceValue = chatChip.GetComponent<Button>();
        tso.FindProperty("lobbyChipButton").objectReferenceValue = lobbyChip.GetComponent<Button>();
        tso.FindProperty("chatUI").objectReferenceValue = chatUI;
        tso.ApplyModifiedProperties();
    }

    private static GameObject CreateHotkeyChip(Transform parent, string key, string label, float width, Font font, bool clickable)
    {
        GameObject chip = CreateUIElement("Chip_" + key, parent);
        chip.AddComponent<LayoutElement>().preferredWidth = width;
        Image bg = chip.AddComponent<Image>();
        bg.color = new Color(0.16f, 0.16f, 0.18f, 0.95f);
        bg.raycastTarget = clickable;
        if (clickable) chip.AddComponent<Button>();

        float capW = Mathf.Max(24f, 11f * key.Length + 10f);
        GameObject cap = CreateUIElement("KeyCap", chip.transform);
        RectTransform capRt = cap.GetComponent<RectTransform>();
        capRt.anchorMin = new Vector2(0, 0.5f);
        capRt.anchorMax = new Vector2(0, 0.5f);
        capRt.pivot = new Vector2(0, 0.5f);
        capRt.sizeDelta = new Vector2(capW, 20);
        capRt.anchoredPosition = new Vector2(6, 0);
        Image capImg = cap.AddComponent<Image>();
        capImg.color = new Color(0.86f, 0.82f, 0.72f);
        capImg.raycastTarget = false;

        GameObject keyObj = CreateUIElement("Key", cap.transform);
        Text keyTxt = keyObj.AddComponent<Text>();
        keyTxt.font = font;
        keyTxt.text = key;
        keyTxt.fontSize = 13;
        keyTxt.fontStyle = FontStyle.Bold;
        keyTxt.color = new Color(0.1f, 0.09f, 0.08f);
        keyTxt.alignment = TextAnchor.MiddleCenter;
        keyTxt.raycastTarget = false;
        StretchToParent(keyObj.GetComponent<RectTransform>());

        GameObject labelObj = CreateUIElement("Label", chip.transform);
        Text labelTxt = labelObj.AddComponent<Text>();
        labelTxt.font = font;
        labelTxt.text = label;
        labelTxt.fontSize = 14;
        labelTxt.color = new Color(0.88f, 0.85f, 0.78f);
        labelTxt.alignment = TextAnchor.MiddleLeft;
        labelTxt.horizontalOverflow = HorizontalWrapMode.Overflow;
        labelTxt.raycastTarget = false;
        RectTransform lRt = labelObj.GetComponent<RectTransform>();
        StretchToParent(lRt);
        lRt.offsetMin = new Vector2(capW + 14, 0);
        return chip;
    }

    private static GameObject CreateUIElement(string name, Transform parent)
    {
        GameObject go = new GameObject(name, typeof(RectTransform));
        go.transform.SetParent(parent, false);
        return go;
    }

    private static void StretchToParent(RectTransform rt)
    {
        rt.anchorMin = Vector2.zero;
        rt.anchorMax = Vector2.one;
        rt.offsetMin = Vector2.zero;
        rt.offsetMax = Vector2.zero;
    }

    private static GameObject CreateButton(string name, Transform parent, string text, Color btnColor)
    {
        GameObject btnObj = CreateUIElement(name, parent);
        Image img = btnObj.AddComponent<Image>();
        img.color = btnColor;
        Button btn = btnObj.AddComponent<Button>();

        GameObject txtObj = CreateUIElement("Text", btnObj.transform);
        Text t = txtObj.AddComponent<Text>();
        t.text = text;
        t.fontSize = 12;
        t.fontStyle = FontStyle.Bold;
        t.alignment = TextAnchor.MiddleCenter;
        t.color = Color.white;
        t.raycastTarget = false;
        StretchToParent(txtObj.GetComponent<RectTransform>());

        return btnObj;
    }

    private static GameObject CreateInputField(string name, Transform parent, string placeholderText)
    {
        GameObject inputObj = CreateUIElement(name, parent);
        Image bgImg = inputObj.AddComponent<Image>();
        bgImg.color = new Color(0.12f, 0.13f, 0.15f);

        InputField inputField = inputObj.AddComponent<InputField>();

        GameObject textObj = CreateUIElement("Text", inputObj.transform);
        Text t = textObj.AddComponent<Text>();
        t.fontSize = 12;
        t.color = Color.white;
        StretchToParent(textObj.GetComponent<RectTransform>());
        textObj.GetComponent<RectTransform>().offsetMin = new Vector2(8, 2);
        textObj.GetComponent<RectTransform>().offsetMax = new Vector2(-8, -2);

        GameObject phObj = CreateUIElement("Placeholder", inputObj.transform);
        Text ph = phObj.AddComponent<Text>();
        ph.text = placeholderText;
        ph.fontSize = 12;
        ph.fontStyle = FontStyle.Italic;
        ph.color = new Color(0.55f, 0.55f, 0.55f, 0.7f);
        StretchToParent(phObj.GetComponent<RectTransform>());
        phObj.GetComponent<RectTransform>().offsetMin = new Vector2(8, 2);
        phObj.GetComponent<RectTransform>().offsetMax = new Vector2(-8, -2);

        inputField.textComponent = t;
        inputField.placeholder = ph;

        return inputObj;
    }
}
