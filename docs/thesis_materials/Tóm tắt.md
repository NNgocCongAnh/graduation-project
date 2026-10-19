# Tóm tắt 

Đề tài “trò chơi trinh thám giải đố trên Web sử dụng LLM tạo bộ hồ sơ vụ án tự động” đòi hỏi một **hệ thống nhiều thành phần** : giao diện ReactJS, API Back-end (FastAPI/Python), kho dữ liệu (PostgreSQL), và dịch vụ AI (LLM qua API hoặc mô hình mở). Hệ thống nên thiết kế theo kiến trúc client-server, trong đó backend chịu trách nhiệm khởi tạo và quản lý cuộc chơi, gọi LLM để sinh nội dung, đồng thời lưu trữ trạng thái trong cơ sở dữ liệu. Việc sinh vụ án sẽ thực hiện theo **quy trình nhiều bước (pipeline)** : lần lượt tạo hồ sơ nạn nhân, nghi phạm, chứng cứ, diễn biến thời gian, đối thoại… nhằm đảm bảo tính logic. Mỗi bước được thiết kế theo **cấu trúc JSON/schema** để LLM trả về kết quả có định dạng rõ ràng, dễ kiểm soát. Sau khi sinh xong, hệ thống thực hiện **kiểm tra tính nhất quán** (dựa trên luật, bộ kiểm tra, thậm chí truy vấn LLM như “thẩm phán logic”) để loại trừ mâu thuẫn (chẳng hạn thời gian chết, chứng cứ, lời khai hợp lý). 

Phương án đề xuất là **pipeline tuần tự có gắn bộ kiểm tra** chứ không dùng hoàn toàn multi-agent phức tạp. Phương án này hợp với một sinh viên đơn lẻ (4 tháng) vì dễ hiện thực, dễ debug, và vẫn có chiều sâu nghiên cứu (như thiết kế pipeline tạo nội dung với ràng buộc, và module validator đảm bảo logic). Kiến trúc đề xuất: ReactJS xử lý giao diện/gameplay; FastAPI làm giao diện API; PostgreSQL lưu trạng thái và nội dung vụ án; có thể dùng thêm Vector DB (như Pinecone) để lưu vector embedding phục vụ truy vấn RAG nếu cần, hoặc Redis cache cho hiệu năng. LLM ưu tiên dùng API chất lượng (GPT-4o, Gemini, Claude) do tập trung vào chất lượng câu trả lời; cũng có thể tích hợp mô hình mở (như Llama3, Mistral) cho giải pháp offline, phụ thuộc tài nguyên và chi phí. Dùng Docker để triển khai. 

Cuối cùng, báo cáo này sẽ chi tiết từng khía cạnh: kiến trúc hệ thống, pipeline sinh vụ án, đảm bảo tính nhất quán, thiết kế đa đại lý so với pipeline, tính định tính lặp lại, mô hình dữ liệu, thành phần AI, kế hoạch triển khai 4 tháng, ước lượng nỗ lực và rủi ro, nghiên cứu liên quan, cách đánh giá sản phẩm và chuẩn bị bảo vệ, rồi đề xuất phương án tốt nhất kèm ví dụ minh hoạ (prompt + JSON schema). 

## 1. Kiến trúc hệ thống (System Architecture) 

Thiết kế hệ thống theo kiến trúc **đa tầng client-server** là hợp lý. Thành phần chính gồm: 

- **Frontend (ReactJS Web Client)** : giao diện chơi game, hiển thị thông tin vụ án, cho phép người chơi tương tác (đọc hồ sơ, phỏng vấn nhân vật, chọn hung thủ, …). 

- **Backend (FastAPI)** : API server xử lý logic chính của trò chơi. Các endpoint như /new_case, /get_case, /guess_suspect… được implement để điều phối trò chơi. Backend giữ vai trò điều khiển luồng trò chơi, gọi dịch vụ AI, lưu/truy vấn cơ sở dữ liệu và trả về kết quả cho frontend. 

- **AI Service (LLM API)** : có thể gọi trực tiếp từ backend qua OpenAI API (GPT-4o, GPT-4 Turbo, Gemini Pro,…), Google Gemini API, hoặc mô hình chạy cục bộ (ví dụ Llama3, Mistral) qua Hugging Face, Ollama. Thành phần này sinh nội dung như hồ 



<!-- Start of picture text -->
Frontend<br>React Web Client<br>a<br>FastAPl Server<br>* r 1 7 a *<br>PostgreSQL Redis Cache Logging/Manitoring | Task Queue<br>| }<br>se rs<br>LLM ServiceyvAPI1<br>\<br>Vector DB (Pinecone)<br><!-- End of picture text -->

- _React Client_ : Cung cấp giao diện trò chơi. Ví dụ: màn hình hiển thị hồ sơ nạn nhân, danh sách nghi phạm (có kèm tiểu sử cơ bản), form đưa ra giả thuyết. Đảm bảo UI thân thiện để nhấn mạnh trải nghiệm trinh thám. Không tốn nhiều thời gian (giống CRUD thông thường + đồn điều) nhưng cần trực quan. 

- _FastAPI_ : Phổ biến, dễ triển khai Docker, hỗ trợ lập trình REST API kiểu Python quen thuộc. Chịu trách nhiệm chính như “brain” của trò chơi. Khi người chơi yêu cầu (ví dụ bắt đầu vụ án mới), FastAPI gọi LLM tạo dữ liệu, lưu DB, trả dữ liệu cho frontend. Cũng lo kiểm tra quyền (nếu có auth), kiểm soát phiên chơi. 

- _LLM Service_ : Có thể trực tiếp tích hợp gọi API (OpenAI/Gemini) trong FastAPI, hoặc tách thành microservice để độc lập phát triển (nhất là nếu dùng mô hình mở). Đóng vai trò **“nhà văn AI”** : tạo hồ sơ nhân vật (nạn nhân, nghi phạm), mô tả hiện trường, timeline, lời khai, báo cáo pháp y, v.v. Chú ý: thiết lập temperature=0 để kết quả ổn định, có thể lặp lại【25†L386-L392】. 

- _PostgreSQL_ : Lưu vĩnh viễn các đối tượng (Case, Character, Evidence, Events). Ví dụ, bảng Case chứa ID, tiêu đề, trạng thái; bảng Character chứa tên, vai trò (víctim/suspect/witness), đặc điểm; bảng Evidence chứa mô tả chứng cứ, liên kết đến Case; bảng TimelineEvent chứa sự kiện và thời gian xảy ra. Các bảng kết hợp thể hiện mối quan hệ 1-n, nhiều-nhiều (ví dụ một vụ án có nhiều nghi phạm, nhiều chứng cứ). Bảng này cũng lưu lịch sử đáp án, đáp án người chơi… để bảo vệ hồ sơ. 

- _Vector DB (tuỳ chọn)_ : Nếu cần RAG, ta lưu embedding của các đoạn văn quan trọng (ví dụ embedding mô tả vụ án, lời khai) để truy vấn tương tác. Ví dụ: dùng trả lời gợi ý hay so sánh new_data với các khám nghiệm, như Luk Verhelst triển khai GraphRAG lưu triples cho truy vấn【34†L55-L59】. 

- _Cache/Queue_ : Redis có thể là cache session hoặc backend queue. Nếu pipeline LLM mất thời gian, tốt nhất push task vào hàng đợi và trả lời UI ngay bằng “Đang tạo vụ án…”. Tổ chức như micro-batching giúp app không treo. 

- _Logging/Monitoring_ : quan trọng cho phát hiện lỗi logic hoặc đáp ứng của LLM (như Emergent Mind nêu làm multi-LLM pipeline dùng cross-check và logging【12†L40L48 】 để nâng cao độ tin cậy). Tích hợp profiling cho endpoint LLM, cảnh báo tốc độ chậm hay API lỗi. 

**Tóm lại** , kiến trúc đề xuất là một hệ thống React – FastAPI – LLM với DB phía sau, có thêm VectorDB và Redis/Queue để tối ưu hiệu năng. Cách phân tách rõ ràng cho phép bạn tập trung phát triển từng thành phần độc lập (giao diện React, logic FastAPI, thiết kế schema JSON cho LLM). Ví dụ dự án LLM multi-agent cũng dùng cấu trúc riêng cho game loop và giao tiếp【25†L386-L394】. Với 4 tháng và 1 dev, kiến trúc này hợp lý: đủ linh hoạt, vừa dễ debug, vừa có thể mở rộng (có thể thêm LLM khác, mở rộng tính năng) mà không quá phức tạp. 

## 2. Quy trình sinh vụ án (Case-Generation Pipeline) 

Để sinh ra “bộ hồ sơ vụ án có tính logic nhất quán”, ta nên chia thành **nhiều bước tuần tự** thay vì “xin xào” 1 prompt duy nhất. Các phương án có thể xem xét: 

- **Pipeline nhiều bước (Multi-step)** : Ví dụ, bước 1 tạo _nạn nhân_ (thông tin cơ bản), bước 2 tạo _danh sách nghi phạm_ , bước 3 xác định _kẻ giết người_ , bước 4 tạo _timeline_ (sự kiện liên quan: thời gian chết, hành động của nghi phạm, lời khai nhân chứng), bước 5 tạo _báo cáo pháp y, hiện trường, chứng cứ_ , v.v. Mỗi bước gọi LLM riêng kèm đầu vào là kết quả bước trước và các ràng buộc cần thiết. Ưu điểm: có thể can thiệp, kiểm soát từng khúc, dễ theo dõi logic. Nhược: phải xây dựng luồng, có thể chậm do nhiều lần gọi API. Độ trễ mỗi lần ~ vài giây, tổng ~10-20s/phiên, có thể chấp nhận cho MVP. 

- **Single-shot / Sequential generation** : Một prompt duy nhất yêu cầu LLM tạo cả bộ hồ sơ. Ưu: dễ triển khai (gửi một lượt, parse JSON). Nhược: độ khó cao, LLM thường bỏ sót thông tin hoặc mâu thuẫn, ít kiểm soát được cấu trúc. Nếu dùng tính năng Structured Output (JSON schema) hay Function Calling, độ tin cậy có thể cải thiện nhưng vẫn rủi mâu thuẫn logic. Nhiều nghiên cứu khuyến cáo tách nhỏ yêu cầu để LLM tập trung hơn【28†L259-L268】. 

- **Structured Output / JSON Schema** : Dù thế nào, ta nên **định nghĩa schema JSON rõ ràng** cho từng phần (ví dụ đoạn JSON cho victim, suspects, evidence). LLM có xu hướng tuân thủ yêu cầu trả JSON nếu được hướng dẫn “Trả lời dưới dạng JSON như mẫu… chỉ trả JSON”【28†L259-L268】. Ví dụ ở [28], nghiên cứu đã ép GPT chỉ sinh dữ liệu theo cấu trúc JSON mong muốn để dễ parse tự động. Cách này giảm thiểu lỗi định dạng và giúp pipeline có thể nối từng bước với nhau. 

- **Function Calling** : Nếu dùng OpenAI GPT-4 API mới, có thể đăng ký một “function” (hàm) với schema JSON và để model trả về JSON-caller. Kỹ thuật này tương tự JSON schema nhưng có hỗ trợ của API, giúp model biết rõ phải sinh ra JSON cho hàm nào 【14†L9-L17】. Tuy nhiên tính năng này chỉ dùng được với GPT-4 hoặc các đời model cao. 

- **RAG (Retrieval-Augmented Generation)** : Thông thường RAG dùng để bổ sung thông tin từ kho tri thức bên ngoài. Ở đây ta có thể dùng RAG trong bước “kiểm tra” hoặc “bổ sung”: giả sử có một vector DB chứa các ví dụ vụ án mẫu hoặc dữ liệu chuyên ngành (forensic reports, hướng dẫn trinh thám), ta có thể truy vấn RAG để tăng tính thực tế. Nhưng với mục tiêu MVP, RAG không bắt buộc (quan trọng nếu muốn thêm bối cảnh thực). 

- **Constraint-based Generation** : Có thể thêm các ràng buộc logic trong prompt từng bước (ví dụ “thời gian chết phải sau khi hung thủ đi vào phòng”, hoặc “tuổi nạn nhân và nghi phạm phải phù hợp”). LLM hiện chưa hỗ trợ constraint solver nghiêm ngặt, nhưng ta có thể **post-validate** : sau khi LLM trả JSON bước nào, chạy các luật kiểm tra. Nếu vi phạm, ta có thể gọi lại LLM chỉnh sửa hoặc chỉnh sửa thủ công. Đây sẽ là phần “validator” riêng (xem phần 3). 

- **Multi-agent generation** : Ý tưởng là sử dụng nhiều LLM đóng vai khác nhau (mỗi agent chịu trách nhiệm tạo một phần: ví dụ “AgList Suspect”, “AgGenerate Evidence”). Công cụ như LangGraph hoặc LangChain Agents có thể hỗ trợ. Như ví dụ dự án “Murder Mystery Agent” (Nir Diamant) đã triển khai game loop với nhiều agent bằng LangGraph【25†L386-L394】. Tuy nhiên, design này phức tạp, tiêu tốn 

thời gian phát triển (4 tháng 1 sinh viên khó đủ). Nó phù hợp với dự án lớn, nhưng cho MVP thì nên tập trung pipeline tuần tự. 

#### **So sánh ưu/nhược** : 

|Chiến lược|Ưu điểm|Nhược điểm|
|---|---|---|
|Pipeline nhiều bước|Kiểm soát logic chặt<br>chẽ, dễ debug, module<br>hóa|Tốn thời gian gọi nhiều<br>lần, phức tạp fow|
|Single-shot (one<br>prompt)|Nhanh, code đơn giản|Dễ mâu thuẫn, khó<br>parse, khó đảm bảo<br>logic tổng thể|
|Structured JSON|Kết quả dễ parse, rõ<br>ràng|LLM có thể bỏ sót/sai<br>schema, cần hướng<br>dẫn kỹ lưỡng【28†L259-<br>L268】|
|Function Calling|Giúp tuân thủ kiểu dữ<br>liệu, có hỗ trợ native<br>API|Chỉ dùng được với<br>model mới, cấu hình<br>phức tạp|
|Multi-agent|Mô phỏng tương tác tự<br>nhiên|Cực phức tạp,<br>overhead, ít cần thiết<br>cho MVP|



**Đề xuất:** Nên **xây dựng pipeline nhiều bước tuần tự với schema JSON ở mỗi bước** , kết hợp kiểm tra tính nhất quán sau mỗi bước. Cụ thể: 

1. **Khởi tạo khung** : Người chơi chọn _“seed”_ (ví dụ: môi trường, số lượng nhân vật, độ khó). Backend tạo GenerateGameState ban đầu. 

2. **Tạo nhân vật** : Dùng LLM sinh thông tin _nhân vật_ (nạn nhân, nghi phạm, nhân chứng) theo schema Character đã định nghĩa (ví dụ giống code ở [25]). Xác định ngẫu nhiên một nghi phạm thành “hung thủ”. 

3. **Tạo timeline và quan hệ** : Dựa vào danh sách nhân vật vừa tạo, gọi LLM tạo _timeline sự kiện_ , mỗi sự kiện kèm thời gian. Kết quả trả về theo định dạng JSON (mảng events). 

4. **Tạo hiện trường và chứng cứ** : Gọi LLM sinh mô tả _hiện trường_ , _chứng cứ vật lý_ (dưới dạng JSON). 

5. **Tạo đối thoại / báo cáo** : Sinh lời khai nhân chứng, thám tử (luồng đối thoại) nếu cần. Có thể dùng LangChain Memory để giữ lịch sử. Kết quả cũng xuất JSON (mảng messages). 

6. **Kiểm tra tổng thể** : Cuối cùng, chạy module validator (phần sau) để kiểm tra toàn bộ JSON sinh ra hợp lý: thời gian không xung đột, chứng cứ khớp hung khí, nhân vật khớp từng lời khai, v.v. Nếu phát hiện mâu thuẫn, có thể gán lại (VD: nếu đối thoại nói hung thủ màu xanh, nhưng timeline nghi phạm 2 màu đỏ thì sửa). 

Mỗi bước sẽ gồm một gọi API LLM (ví dụ function create_characters(), create_timeline()…). Đầu ra JSON từ bước trước được truyền làm input cho bước sau, đảm bảo sự liên kết. Kỹ thuật này tương tự như trong luận văn của Barros et al. (2018) – tuy dùng dữ liệu mở – nhưng họ cũng tuần tự tìm kiếm nghi phạm, alibi, kết nối dữ liệu để sinh game【19†L18L26】. Ở đây, LLM thay thế việc khai thác Wikipedia/OSM. Như trong [28], việc ép LLM xuất JSON đúng khuôn mẫu giúp tự động xử lý và tránh giải thích thừa【28†L259-L268】. 

## 3. Đảm bảo tính nhất quán và logic (Consistency & Logic Assurance) 

Mục tiêu là bộ hồ sơ vụ án sinh ra **không có mâu thuẫn nội tại** . Ví dụ: thời gian chết, nơi phát hiện, lời khai và chứng cứ phải khớp nhau. Các kỹ thuật bổ trợ: 

- **Rule-based checks (Luật cứng)** : Sau khi có dữ liệu từ LLM, áp các quy tắc luật: 

- **Kiểm tra timeline** : ví dụ “thời gian chết” phải lớn hơn giờ cuối gặp nạn nhân với hung thủ; các sự kiện phải được sắp xếp thời gian hợp lý. 

- **Độ tuổi/đặc điểm** : Số tuổi nhân vật phải hợp lý (nhân chứng không thể bé hơn thiếu niên, hung thủ có động cơ phù hợp, v.v.) 

- **Không gian** : Khoảng cách địa lý của hiện trường, nơi nghi phạm xuất hiện phải khả thi. 

- **Động cơ/lời khai** : Phải không mâu thuẫn (ví dụ hung thủ không thú nhận phạm tội, nhưng lời khai LLM tạo ra đôi khi vô tình cho hung thủ có alibi… phải sửa). Ví dụ, nếu JSON có time_of_death: "21:30" nhưng lời khai nhân chứng nói “vụ án xảy ra lúc 22:00”, ta phát hiện xung đột. Luật cứng này có thể cài trong code (validator) kiểm tra điều kiện. 

- **Graph/Knowledge-based validation** : Xây dựng đồ thị tri thức (Knowledge Graph) từ thông tin vụ án. Mỗi nhân vật, chứng cứ, sự kiện là một node; quan hệ (“có alibi”, “sở hữu hung khí”, “xuất hiện ở hiện trường lúc …”) là cạnh. Sau đó chạy phân tích như GraphRAG: phát hiện thành phần nào thiếu, bất đồng. Như Luk Verhelst nêu, GraphRAG mạnh nhờ **lấy các mối quan hệ cấu trúc** (ví dụ: _Motivation: A tin/vì B, Alibi: A ở nơi khác…_ ), giúp suy luận tính chính xác【34†L55-L59】. Có thể áp dụng đồ thị cực đơn giản: nối hung khí với hung thủ, etc., dùng luật trên đồ thị để rà soát vòng tròn logic. 

- **Validator (rule-engine)** : Dùng bộ kiểm tra (validator) riêng. Ví dụ: viết một hàm validate_case(case_json) trả về danh sách lỗi logic (xung đột thời gian, loại trừ chứng cứ mâu thuẫn, v.v.). Nếu lỗi, bot có thể tự động sửa hoặc báo cho người phát triển. Đôi khi ta có thể cho LLM “tự xét lại” (LLM-as-judge): hỏi LLM “Kiểm tra xem hồ sơ vụ án có mâu thuẫn không, nếu có hãy chỉnh sửa”. Nghiên cứu đã chỉ ra khả năng LLM dùng NLI (Natural Language Inference) để xác định mâu thuẫn【12†L54-L63】. Ta có thể tự hỏi LLM như một “thẩm phán AI” trước khi hoàn thiện. 

- **Unit tests (Kiểm thử tự động)** : Tạo các kịch bản đơn giản kiểm tra tính nhất quán. Ví dụ, cho LLM tạo nhiều ca thử nghiệm và chạy các hàm test: “Nếu hung thủ là X, 

thì trong timeline X phải xuất hiện tại hiện trường; nếu lời khai khẳng định Y, phải có mâu thuẫn phản chứng”. Mục tiêu đảm bảo “không có lỗi logic cơ bản nào còn sót”. 

- **Phân tích đối thoại và kế hoạch (Story logic)** : Nếu phần game có tương tác nhân vật (phỏng vấn), cần giữ memory (ví dụ LangChain Memory) để nhân vật trả lời nhất quán. Theo [25], các hàm tạo đối thoại cho nhân vật cố gắng **“không tiết lộ vai trò, không tự tranh minh”** khi giới thiệu【25†L399-L408】. Tức là nhân vật biết thân thế, nhưng AI phải ensure họ “không tự thú” hoặc nói lặp lại, tránh mâu thuẫn trong lời nói. 

**Tóm lại** , ngoài prompt tốt, **chúng ta cần module kiểm tra** . Chẳng hạn, sau khi LLM trả JSON, gọi hàm kiểm tra mọi trường hợp sai logic. Nếu phát hiện: sửa JSON (có thể đòi LLM lặp lại bước đó với prompt nhắc lại lỗi) hoặc loại bỏ phương án. Có thể sử dụng ý tưởng _multi-LLM pipeline_ như EmergentMind (2026) – phối hợp tự kiểm tra nội tại (selfconsistency), đối chiếu nguồn tài liệu (extrinsic check), và cả đồ thị đối tượng để đảm bảo tính nhất quán【38†L1-L4】. Dự án RAG giải Rue Morgue cũng cho thấy lưu trữ thông tin dưới dạng triple giúp kiểm tra logic “Dupin có động cơ, không có alibi, giả danh…”【34†L55-L59】. Chúng ta không cần tốn công xây GraphRAG hoàn chỉnh, nhưng ý tưởng về đồ thị logic là hữu ích để xác định mấu chốt (ví dụ nạn nhân-kẻ-động_cơ-chứng_cứ phải kết nối thành chuỗi hợp lý). 

## 4. Multi-Agent vs Pipeline 

**Multi-agent approach** : Ý tưởng là gán mỗi LLM một “vai” (agent) riêng: ví dụ một agent chuyên tạo nhân vật, một agent tạo timeline, một agent tạo đối thoại (như **Murder Mystery Agent** dùng LangGraph【25†L386-L394】), hoặc dùng LLM như “Sherlock AI” để phỏng vấn nhân vật. Multi-agent có thể tự nhiên mô phỏng tương tác, cho phép mỗi agent chỉ tập trung một nhiệm vụ, và có thể cho tương tác khứ hồi giữa agents. Tuy nhiên, nhược điểm rất lớn: phức tạp trong thiết kế (cần framework điều phối như LangGraph/LangChain, đòi hỏi coordinate state giữa các agents) và **thời gian triển khai gấp rưỡi** . Thêm nữa, Multiagent thường đòi hỏi nhiều hàm gọi lẫn nhau, gây khó debug (lỗi logic ở step nào không rõ). Các nghiên cứu về Jubensha (một trò trinh thám nhiều người chơi) mới chỉ thử nghiệm LLM làm agent riêng biệt để trả lời câu hỏi trong kịch bản【36†L63-L71】, nhưng không phải sinh câu chuyện từ đầu. 

**Single-agent (pipeline)** : Mỗi bước là một call đến LLM (FastAPI thực hiện tuần tự). Ưu điểm: đơn giản, dễ kiểm soát luồng, có thể dùng cùng một model hoặc chút logic điều phối. Các dự án khảo sát đề xuất dạng pipeline vì dễ theo dõi và đảm bảo chất lượng hơn so với để LLM “cảm tính” tự phát triển cả trò chơi một lần【28†L259-L268】. Với một sinh viên 4 tháng, nên ưu tiên pipeline. 

**Kết luận:** Đối với MVP 4 tháng, chọn _pipeline tuần tự_ . Multi-agent chỉ nên dùng nếu có nhiều thời gian, nhưng vừa rồi đã có hướng dẫn cách tận dụng JSON schema để thu gọn issue mà không cần quá nhiều agents【25†L339-L347】. Nếu thời gian cho phép, có thể mô phỏng agent cho phần gameplay (ví dụ “SherlockAI” đỡ người chơi hỏi nhân vật), nhưng phần sinh dữ liệu (tạo case) vẫn dùng pipeline. 

## 5. Tính định tính (Determinism & Reproducibility) 

Muốn kết quả **nhất quán** giữa các lần chạy (giúp debug, tái tạo lỗi), ta cần chú ý: 

- **Khóa seed / nhiệt độ** : Với các API LLM (GPT-4, Gemini), không có seed trực tiếp, nhưng **đặt temperature=0** sẽ cho kết quả ổn định (như dự án mẫu đã làm 【25†L386-L392】). Tương tự, với mô hình cục bộ có thể set seed và disable sampling (top-k=1). Điều này giúp mỗi lời gọi API tương tự nhau (khi prompt giống hệt). 

- **Phiên bản model cố định** : Xác nhận dùng một phiên bản model và giữ nguyên trong suốt dự án (ví dụ luôn dùng GPT-4o-0613). Nếu model update, kết quả có thể khác. Có thể lưu backup local của mô hình hoặc phiếu cấu hình ứng dụng để tránh thay đổi ngầm. 

- **Phiên bản prompt/schema** : Lưu lại lịch sử prompt, quy định schema (ví dụ dùng YAML/Pydantic để định nghĩa các cấu trúc JSON). Đảm bảo mọi thay đổi về prompt hay schema được ghi chú (giống code version, hoặc ghi trong DB) để đối chiếu. 

- **Chiến lược decode deterministic** : Ngoài temp=0, có thể dùng stream=false, top_p=0 để bắt buộc model chọn token có xác suất lớn nhất; hoặc với models có hỗ trợ (llama.cpp Jacobi decoding) để sinh song song không gốc. Mục đích là tránh randomness. 

- **Hệ thống kiểm soát và log** : Ghi lại log đầy đủ: prompt gửi đi, response JSON nhận được, thời gian tạo. Dùng logging file hoặc xuất ra DB để dễ replay. Nếu có lỗi, có thể lấy log và chạy lại từng bước để tra. 

- **Kiểm thử và seed input** : Tạo sẵn một số “seed case” (ví dụ nạn nhân/vụ án mẫu) để dùng làm test. Đảm bảo cho cùng input seed, pipeline luôn cho cùng output. Kiểm tra tự động qua unit test (ví dụ dùng pytest) mỗi khi thay đổi code. 

Các bước này đảm bảo rằng kết quả tạo ra có tính lặp lại cao. Ví dụ dự án mẫu đã dùng GPT4-o với temp=0 cho determinism【25†L386-L392】. Ngoài ra, ta có thể xây khung “phát hiện drift” khi model trả các cấu trúc khác kỳ vọng để xem có sự sai lệch do update API. 

## 6. Mô hình dữ liệu (Data Model) 

Về cơ sở dữ liệu, ta có thể thiết kế **ER Diagram** các bảng chính: 

- **Case** : (CaseID, Tiêu đề, Mô tả sơ bộ, trạng thái, thời gian tạo, v.v.) – đại diện cho một vụ án. 

- **Character** : (CharID, CaseID, Tên, Vai trò (victim/suspect/witness), Tuổi, Mối quan hệ, Tiểu sử). Một Case có nhiều Character (1-n). Ví dụ Char.role = 'victim' (nạn nhân), hoặc 'suspect', 'witness'. 

- **Relationship** (tùy chọn): bảng nối để lưu quan hệ giữa hai Character (ví dụ quan hệ gia đình, làm ăn) nếu cần phức tạp. Mối quan hệ này cũng có thể do LLM sinh ra. 

- **TimelineEvent** : (EventID, CaseID, thời gian, mô tả). Mỗi Case có một danh sách timeline (1-n). Ví dụ: “21:30 – Nạn nhân bị sát hại”, “22:00 – Cảnh sát có mặt tại hiện trường”. 

- **Evidence** : (EvidenceID, CaseID, loại (Hung khí, chứng cứ vật lý, giấy tờ…), mô tả, phát hiện tại CharacterID hay địa điểm nào). Ví dụ evidence có thể liên kết đến Character (charID nếu là vật của ai đó). 

- **Dialogue/Log** : (LogID, CaseID, CharID, nội dung/phút hội thoại) – lưu lại các đoạn đối thoại khi chơi (nếu cần lưu lịch sử). 

- **User/Session** (nếu có authentication): để lưu người chơi, điểm số hoặc phiên. Nhưng không bắt buộc nếu tập trung vào kỹ thuật AI. 

Mermaid ER mẫu đơn giản có thể như sau: 



<!-- Start of picture text -->
CASE<br>int id PK<br>string title<br>_ string escription ae<br>aow ae<br>Pe aE iea<br>ro / om ,es<br>|| (_}| vyi<br>aa CHARACTER<br>|| hy<br>| TIMELINE_EVENT<br>int id P<br>int id PK<br>int case_id FI<br>int case_id FK<br>datetime time<br>| string | name<br>| string = role<br>| string description<br>\ string | details<br>\ \ \¥\<br>4i<br>,<br>\<br>Ny ry<br>%=<br>~we att<br>ee a<br>eum EVIDENCE ae<br>g e,<br>int id PK 7<br>int case_id FR<br>string type<br>string description<br>int found_by_char | FK<br><!-- End of picture text -->

7. Thành phần AI và công cụ sử dụng (AI Components) 

   - **LLM API** : Ưu tiên GPT-4o (hoặc GPT-4 Turbo) của OpenAI, hoặc Google Gemini thế hệ mới (như Gemini Pro). Các model này có khả năng hiểu ngữ cảnh phức tạp và duy trì mạch truyện tốt. Tham khảo [25] thấy họ dùng GPT-4o để đảm bảo nội dung chất lượng và deterministic (temp=0). Cũng có thể dùng Claude-3 nếu muốn, nhưng GPT-4o hiện phổ biến nhất. Chi phí API OpenAI: khoảng $0.15–0.30/1K token (xem giá mới), cỡ 1K token đủ cho bài toán dài (~ vài trăm câu). Nếu muốn giảm phí, có thể dùng một phần nội dung generator sử dụng Llama3/Mistral cài qua Ollama/HF, nhưng điều này phức tạp và có thể giảm độ chính xác. Đối với MVP, dùng OpenAI hoặc Gemini để đảm bảo. 

   - **Mô hình cục bộ (nhúng)** : Là tùy chọn. Nếu không muốn phụ thuộc API, có thể tải Llama3 32k hoặc Mistral 7B, fine-tune đôi chút (tốn thời gian). Có thể dùng Ollama/HuggingFace Transformers. Ưu: offline, không mất phí cho mỗi lần gọi. Nhược: không xử lý nội dung dài tốt như GPT-4o, cấu hình môi trường Docker phức. 

   - **Embeddings & Vector DB** : Nếu muốn tích hợp RAG (ví dụ tìm các ví dụ câu chuyện tương tự từ dữ liệu cũ hoặc giải thích), ta tạo embedding cho từng phần văn bản quan trọng và lưu vào Pinecone/Weaviate. RAG có thể dùng tìm hiểu tương quan, nhưng khả năng cao sẽ ít dùng nếu game chỉ dùng LLM đơn thuần. Nếu cần, có thể lưu embedding từ các bản dịch cũ, lời khai mẫu, để khi tạo mới ta có thể hỏi “LLM này dựa trên ví dụ cũ nào?”. 

   - **Chèn context (Memory)** : Có thể sử dụng LangChain ChatMemory hoặc bộ nhớ tạm nếu trò chơi có phỏng vấn nhiều lượt. Khi nhân vật A nói điều gì, lưu vào memory để khi gọi LLM tiếp theo (đối thoại), nó ghi nhớ. Vd: "CharacterIntros" đã lưu persona của từng Character qua thuộc tính .persona【25†L349-L358】. 

   - **RAG & Retrieval** : Chúng ta có thể tích hợp RAG nếu muốn sản phẩm phong phú hơn (ví dụ mở rộng với tài liệu điều tra). Lấy ví dụ như trong solving Rue Morgue, họ truy xuất văn bản hỗ trợ reasoning【11†L7-L16】. Nhưng với game này, RAG chủ yếu phục vụ sàng lọc logic (e.g. dùng vector DB kiểm tra contradiction như HalluMatDetector) 【12†L96-L104】. 

   - **Tool/Function Calling** : Định nghĩa một hàm giả (ví dụ create_case()) cho phép GPT trả về JSON object, tận dụng chức năng “Function Calling” của GPT-4 API【14†L9L17】. Điều này đảm bảo model cố gắng theo schema hơn. 

   - **Công nghệ triển khai** : Sử dụng FastAPI kèm SQLAlchemy cho DB, LangChain/LLMChain nếu muốn trợ giúp quản lý convo, nhưng có thể code tay do đơn giản. Dockerize toàn bộ (có docker-compose chứa web, backend, db, vector DB nếu cần). Dùng OAuth2/JWT nếu thêm auth. 

Tóm lại, **stack đề xuất** : Python (FastAPI, LangChain), React, PostgreSQL, Docker, kết hợp với OpenAI GPT-4/Gemini. Với 4 tháng, tập trung vào LLM API để tăng tốc phát triển: dự án mẫu và cả tài liệu đều cho thấy việc gọi API LLM là phần dễ dàng nhất【25†L359-L368】 



<!-- Start of picture text -->
Li-trimh phebe: ortin i chang<br>_ ees amies<br>eee<br><!-- End of picture text -->

|Module|Efort|Rủi ro & Biện pháp<br>giảm thiểu|
|---|---|---|
|**Xác thực người dùng**<br>(Auth)|Thấp|(Nếu cần) Triển khai<br>OAuth / JWT. Rủi ro:<br>phụ thuộc thư viện.<br>Giảm thiểu: dùng<br>templates có sẵn.|
|**Backend CRUD & API**|Trung bình|Viết API FastAPI cơ<br>bản. Rủi ro: lỗi API,<br>versioning. Giảm thiểu:<br>document rõ endpoint,<br>dùng swagger.|
|**Generator (LLM)**|Cao|Viết logic gọi LLM,<br>parse JSON. Rủi ro:<br>định dạng sai, logic<br>nhân quả. Giảm thiểu:<br>thiết kế schema chặt,<br>test với mock.|
|**Validator**|Trung bình|Kiểm tra luật, viết hàm<br>test. Rủi ro: bỏ sót kịch<br>bản xung đột. Giảm<br>thiểu: viết unit test đa<br>tình huống, có log chi<br>tiết.|
|**UI React**|Trung bình|Tạo giao diện hiển thị<br>dữ liệu. Rủi ro: bug<br>tương tác, cross-<br>browser. Giảm thiểu:<br>sử dụng component<br>thư viện, test trên<br>nhiều màn hình.|
|**Kết nối Front-Back**|Trung bình|Fetch API, xử lý trạng<br>thái. Rủi ro: lỗi CORS,<br>API trả định dạng không<br>đúng. Giảm thiểu: kiểm<br>thử tích hợp, dùng<br>Postman/Mock Server.|
|**Triển khai (Docker)**|Thấp|Dockerize toàn bộ. Rủi<br>ro: cấu hình môi trường<br>sai, service không liên<br>lạc. Giảm thiểu:<br>docker-compose test|



|Module|Efort|Rủi ro & Biện pháp<br>giảm thiểu|
|---|---|---|
|||local, log cẩn thận.|
|**Kiểm thử & Bảo trì**|Trung bình|Viết kịch bản test, sửa<br>lỗi. Rủi ro: thời gian gấp<br>(giữa bảo vệ). Giảm<br>thiểu: thực hiện test tự<br>động, ưu tiên fx lỗi<br>nghiêm trọng trước.|



Phần quan trọng **Generator (LLM + pipeline)** có rủi ro cao nhất: LLM có thể trả dữ liệu không hợp lệ hoặc mâu thuẫn. Giảm thiểu bằng prompt engineering, schema rõ ràng, tăng test. Mỗi module khác có thể điều chỉnh hoặc thay library nếu vướng. Tổng thể, rủi ro lớn nhất là **logic/story xung đột** . Để đối phó, cần validator tốt và giải thích rõ trong báo cáo. 

## 10. Công trình liên quan (Related Work & Resources) 

Một số nghiên cứu và dự án tham khảo: 

- **WikiMystery (Barros et al. 2018)** 【19†L18-L26】: Hệ thống sinh trò chơi trinh thám từ dữ liệu mở (Wikipedia), pipeline gồm tạo nghi phạm, alibi, bằng chứng… Công trình này cho thấy cấu trúc chung của trò trinh thám (một người bị giết, nhiều nghi phạm, mối quan hệ phải khớp). Mặc dù dùng thuật toán truyền thống, bước sinh theo trình tự tương đồng pipeline ta cần dùng. 

- **Murder Mystery Agent (Nir Diamant, 2024)** 【25†L339-L347】【25†L399-L408】: Dự án GitHub dùng LangGraph và GPT-4 để tạo trò chơi trinh thám, trong đó có sử dụng schema (Pydantic) để bắt JSON và giữ giao tiếp giữa nhiều agent. Họ định nghĩa class StoryDetails (victim, time, etc) cho structured output【25†L359-L368 】 và dùng temperature=0 cho nhất quán【25†L386-L392】. Đây là ví dụ rõ ràng cách ép LLM trả JSON và quản lý game state. 

- **HalluMatDetector / Multi-LLM Pipeline (Vangala et al. 2025, Emergent Mind 2026)** 【12†L40-L48】: Framework sử dụng nhiều LLM phối hợp để kiểm chứng nội dung (self-consistency, graph analysis, external evidence). Tham khảo ý tưởng “LLM-as-judge” và cơ chế kiểm tra chéo để tăng độ tin cậy. Ví dụ: nếu tạo ra 2 lời giải khác nhau, dùng LLM thứ 3 chọn. Các mô-đun intrinsic/extrinsic trong tài liệu này gợi ý cách mình có thể tự check đầu ra LLM. 

- **AI Dungeon (Nick Walton, 2019)** 【32†L39-L47】: Game text adventure mở đầu là dự án nghiên cứu AI. AI Dungeon cho thấy LLM có thể tạo cốt truyện mở (“infinite possibilities”). Giữ được bối cảnh trò chơi trong nhiều lượt tương tác. Bài viết NVIDIA (2022) mô tả cách GPT liên tục xây dựng world cho mỗi input của người chơi. Đây là ví dụ thương mại nổi tiếng về trò chơi GPT-driven mà chúng ta có thể học (như lưu history đối thoại, xử lý input không kịch bản sẵn). 

- **Jubensha AI (Wu et al. 2024)** 【36†L85-L93】【36†L109-L117】: Nghiên cứu đầu tiên về LLM trong trò trinh thám nhiều người (Trung Quốc). Datasets và framework đa-agent 

cho phép nhiều LLM tương tác (memory, self-refinement)【36†L63-L71】. Dù tập trung agent, giấy chỉ ra tính phức tạp của multi-agent trong trò murder mystery – hợp tác thu thập thông tin, suy luận. Không ứng dụng trực tiếp tạo case, nhưng cung cấp khung đánh giá game AI trinh thám (win rate không đủ, cần đánh giá khả năng nắm case, lý luận). 

- **Procedural Narrative (Chawla 2024)** 【28†L259-L268】: Luận văn của SMU Guildhall, một ví dụ trò card-game trinh thám AI. Điểm đáng chú ý: tác giả ép GPT output theo JSON schema để tích hợp vào game, không cho giải thích thừa. Ví dụ: “Return nothing but JSON … don’t reply with anything else”【28†L259-L268】. Và đề cập về việc các stage game sử dụng JSON. Đây là hướng dẫn quý giá cho prompt thiết kế. 

- **CrawLLM (Zammit, Liapis et al., 2026)** 【37†L5-L13】: Hệ thống LLM-driven pipeline tạo game (dungeon-crawler). Họ dùng Mixtral 8x7B để tạo theme, hướng dẫn tạo nội dung. Mặc dù không liên quan trực tiếp trinh thám, mô hình pipeline (theme generation → nội dung → đồ hoạ) cho thấy xu hướng dùng LLM cho content đa dạng trong game. 

- **Unbounded (Li et al. 2024)** : (được nhắc trong Murder Mystery Agent) – game nhập vai generative infinite, nhưng không tìm thấy trích dẫn trực tiếp. 

- **Tools khác** : Ví dụ blog về “Structured Outputs vs Function Calling”【14†L9-L17】, giúp hiểu nên dùng cách nào. 

Các nguồn trên đều có sẵn. **Tất cả dữ liệu tham khảo (papers, blog, GitHub) đều từ 2018 đến 2026** . Mỗi nguồn có thể học: Barros 2018 học cách pipeline, Chawla 2024 học cách ép JSON, Wu 2024 học đánh giá, EmergentMind 2026 học kiểm tra, Diamant 2024 học multimodule game. Các dự án mã nguồn mở (AI Dungeon, NirDiamant) có code tham khảo cho giao diện và gọi LLM. 

## 11. Đánh giá & Chuẩn bị bảo vệ 

**Đánh giá hệ thống:** Để đo lường độ tốt của hệ thống: 

- **Kiểm tra tự động (unit tests)** : Kiểm thử functions validate: feed các case hợp lệ và giả mâu thuẫn (ví dụ: timeline sai thứ tự) và đảm bảo hệ thống nhận ra. 

- **Đánh giá câu chuyện (Story metrics)** : Dùng tiêu chí đơn giản như độ trùng lặp (ngram giảm); đo **độ mới (novelty)** và **phù hợp (coherence)** . Có thể học từ AI Dungeon (150k user) cách lấy feedback. 

- **Thu thập phản hồi người dùng** : Gọi một số bạn sinh viên chơi thử (đọc story, chọn hung thủ). Đo độ chính xác giải đố, cảm nhận tính hấp dẫn. 

- **So sánh với benchmark** : Không có dataset chuẩn, nhưng có thể lấy truy vấn ví dụ từ các puzzle hiện có để thử (ví dụ “Puzzle murder mystery puzzles” trên Kaggle/reddit). 

- **Chuẩn bị demo bảo vệ** : Ví dụ kịch bản cụ thể: bắt đầu từ một “seed”, show tiến trình từng bước: sinh nhân vật, timeline, chứng cứ. Cho phép người bảo vệ “thử lái” (ví dụ nhập một điều kiện, hệ thống sinh ra khác, hoặc kiểm tra tính nhất quán qua câu hỏi). Tình huống demo: “Tìm kẻ giết người dựa vào mớ dữ liệu AI tạo ra”. 

**Câu hỏi bảo vệ** : Dự đoán hội đồng có thể hỏi: 

- _Tại sao sử dụng LLM thay vì đào tạo ML truyền thống?_ (Trả lời: ML truyền thống cần dữ liệu lớn, lâu, chưa chắc được; LLM API cho kết quả ngay, tập trung vào ứng dụng thực tiễn【12†L40-L48】.) 

- _Làm sao đảm bảo LLM không hú vía ra nội dung gây tranh cãi/hội tụ?_ (Trả lời: prompt rõ ràng, JSON schema, temp=0, validator sau sinh. Thêm nữa, phạm vi đề tài hạn chế (truyện trinh thám) nên ít rủi ro.) 

- _Tính toán chi phí (API, compute)?_ (Trả lời: ước tính số token mỗi case, nhân với chi phí API. Nếu dùng local thì dùng GPU hiện có, không tính phí token.) 

- _So sánh với phương án truyền thống (train model từ đầu)?_ (Khẳng định: phương án này tối ưu thời gian, không yêu cầu thu thập data to, thích ứng nhanh.) 

- _Giải thích cách kiểm tra chéo (ví dụ RAG)?_ (Giải thích ý tưởng RAG nếu tích hợp – trường hợp cho HQ interest). 

- _Nếu phát hiện mâu thuẫn logic nặng?_ (Có thể dùng multi-LLM kiểm tra, hoặc fallback: hiện thông báo lỗi, yêu cầu người chơi quyết định có tiếp tục hay tạo lại vụ án mới.) 

- _Khả năng mở rộng: nếu cần thêm 1000 cases/tháng?_ (Chỉ cần scale FastAPI + cache, vector DB; LLM API scale theo request. Docker giúp scale dễ.) 

- _Điểm yếu: LLM có thể “bịa” chữ?_ (Đúng, cần validator. Nếu sản phẩm thương mại, có thể kết hợp chuyên gia review.) 

Kết quả bảo vệ đánh giá quan trọng: **MVP chạy ổn định** và phần “kiểm tra tính nhất quán” được triển khai tốt (đây là đóng góp chính). Demo chắc để tạo 1–2 vụ án mẫu để chứng minh logic, và trả lời thuyết phục các vấn đề trên. 

## 12. Kết luận & Lựa chọn cuối cùng 

Sau khi khảo sát, phương án tối ưu cho một sinh viên đơn lẻ 4 tháng là: 

- **Kiến trúc** : ReactJS + FastAPI + PostgreSQL + Docker (kèm Redis/Queue nếu cần) + LLM (GPT-4o/Gemini). Giải pháp này tiêu chuẩn, nhiều tài liệu, dễ tích hợp và đủ mạnh để thể hiện đề tài.【25†L386-L392】【28†L259-L268】 

- **Pipeline** : Chuỗi generation tuần tự, mỗi bước trả JSON theo schema và validate. Không dùng multi-agent phức tạp. JSON schema/hàm sẽ đảm bảo kết cấu rõ ràng 【28†L259-L268】【34†L55-L59】. 

- **MVP** : Tập trung tính năng tạo ra **một bộ hồ sơ vụ án** đầy đủ, hợp lý, và cho phép người chơi đọc giải đố. Tính năng sau bảo vệ: giao diện đẹp, chức năng bổ sung (đối thoại tự động, multi-case). 

**Hướng phát triển tương lai** : Có thể mở rộng thành sản phẩm thương mại (game mobile/web phiêu lưu), hoặc nghiên cứu bài báo (kiến trúc pipeline AI game). Ta cũng có thể nghiên cứu thêm module “phán đoán của LLM” để kiểm tra câu chuyện (LLM-as-critic), hoặc tích hợp RAG sâu hơn dùng vector DB cho nội dung phức tạp. 

### Ví dụ mẫu (Prompt + JSON Schema) 

Dưới đây là ví dụ minh họa prompt và schema cho bước tạo case đơn giản: 

#### **Prompt (tiếng Việt):** 

Bạn là trợ lý AI sinh một vụ án trinh thám. Đầu ra yêu cầu JSON thuần với cấu trúc: { "victim": {"name": string, "age": number, "time_of_death": string, "location": string}, "suspects": [ {"name": string, "motive": string, "alibi": string}, ... ], "timeline": [ {"time": string, "event": string}, ... ], "evidence": [ {"item": string, "found_at": string, "related_person": string}, ... ], "culprit": string } Hãy đảm bảo tất cả thông tin nhất quán (thời gian, địa điểm, lời khai khớp với bằng chứng). Trả lời **chỉ có JSON**. 

#### **Schema mẫu (pseudo):** 

{ "victim": {"name": "Nạn nhân", "age": 40, "time_of_death": "2026-07-19 21:30", "location": "Văn phòng công ty"}, "suspects": [ {"name": "Nguyễn Văn A", "motive": "Tranh chấp hợp đồng", "alibi": "Đang họp nội bộ lúc 21:30"}, {"name": "Trần Thị B", "motive": "Mối thâm thù cá nhân", "alibi": "Đi dự tiệc bên kia đường"} ], "timeline": [ {"time": "2026-07-19 21:00", "event": "Nạn nhân rời văn phòng đến nhà riêng"}, {"time": "2026-07-19 21:30", "event": "Nạn nhân bị sát hại tại văn phòng công ty"}, {"time": "2026-07-19 21:45", "event": "Cảnh sát được gọi đến và tìm thấy thi thể"} ], "evidence": [ {"item": "Con dao gọt hoa quả", "found_at": "Hiện trường", "related_person": "Trần Thị B"}, {"item": "Hóa đơn cafe", "found_at": "Văn phòng", "related_person": "Nguyễn Văn A"} 

], "culprit": "Trần Thị B" } 

Đây chỉ là ví dụ đơn giản. Trong thực tế, LLM sẽ sinh các giá trị phù hợp và đủ 4 yếu tố trên. Module validator sẽ kiểm tra xem lời khai (ví dụ alibi) và chứng cứ (con dao) có khớp với timeline (21:30 hung thủ ở đâu) hay không, rồi trả ra kết quả cuối cùng. 

**Kết luận:** Với thiết kế trên, ta tin rằng đề tài “trò chơi trinh thám AI trên web” sẽ khả thi trong 4 tháng cho một sinh viên, đồng thời có cả chiều sâu nghiên cứu (thiết kế pipeline, giải quyết vấn đề logic) và giá trị ứng dụng (game demo có thể chơi được). Tiến độ đề xuất, kiến trúc và pipeline này đảm bảo bạn có thể **ra mắt sản phẩm prototype hoàn chỉnh và chất lượng** để tự hào trong buổi bảo vệ. 

