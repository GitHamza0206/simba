# Changelog

## [0.5.0](https://github.com/GitHamza0206/simba/compare/v0.4.0...v0.5.0) (2025-05-12)


### ✨ Features

* add dropdown menu for document management actions ([d2c5e22](https://github.com/GitHamza0206/simba/commit/d2c5e22c13397494884827ef4aa4dbaddbcbc2a8))
* add Knowledge Configuration page and update sidebar ([7a4f5a2](https://github.com/GitHamza0206/simba/commit/7a4f5a2e2c8e1a2d768f64b97ce5e4c3d0cffa8d))
* Add MinIO storage provider ([c1aaed3](https://github.com/GitHamza0206/simba/commit/c1aaed320244a2c336b67a3467bc3a0d78134ba0))
* add react-hot-toast and refactor Knowledge Configuration routing ([e6aca32](https://github.com/GitHamza0206/simba/commit/e6aca32254e80a28fae4461cab6eb9071ab0284b))
* add Redis caching for document management and browser-side caching ([4968d92](https://github.com/GitHamza0206/simba/commit/4968d92310561608edba6dd73dd59f443c4bb47b))
* add settings management with general and members settings pages ([4602a1c](https://github.com/GitHamza0206/simba/commit/4602a1c545329ee1694425738c20094092921e47))
* add text handling methods to PGVectorStore ([6ebb770](https://github.com/GitHamza0206/simba/commit/6ebb770fe8f06f3300e2bb794a709391e122f2ad))
* added migrate as entrypoint to docker ([6462e8d](https://github.com/GitHamza0206/simba/commit/6462e8dfee7e0d754d1019a0a0558ae7e7d82905))
* auth with supabase ([ea34ee6](https://github.com/GitHamza0206/simba/commit/ea34ee640df63fcc0ddde305168cef7ceb870e84))
* CAG with custom graph flow with router and cot ([7e33cc1](https://github.com/GitHamza0206/simba/commit/7e33cc1ecaf9caa50a22b509f73efd7e63df5b0a))
* ci/cd & images pushed to docker hub compatible with supabase external ([d41712e](https://github.com/GitHamza0206/simba/commit/d41712eadb201946e940eef5c6873dd84da28e6c))
* enhance document ingestion and access control ([a3533a8](https://github.com/GitHamza0206/simba/commit/a3533a8c72ef5ef97e8e4439a4b10f5d17c2d7e7))
* enhance document splitting and retrieval in embedding service ([6e127a1](https://github.com/GitHamza0206/simba/commit/6e127a136f6d6875d268034df50a7c42d13256fb))
* enhance state management and message handling ([81bffa8](https://github.com/GitHamza0206/simba/commit/81bffa835b7f42243189a72d375fab69517e3e9d))
* implement API key management and authentication ([89ce8cc](https://github.com/GitHamza0206/simba/commit/89ce8cc634f816c330f8e82bf916e4709dae2946))
* implement API key management features and enhance tenant support ([c32f7c6](https://github.com/GitHamza0206/simba/commit/c32f7c69a595650a21b367e6b06a9cfa8f13d263))
* implement auth system with roles, permissions and organizations ([95b80a5](https://github.com/GitHamza0206/simba/commit/95b80a58d062538df38c3c29679c21ad14d0949b))
* implement storage provider architecture (Local Only) ([b76f1c7](https://github.com/GitHamza0206/simba/commit/b76f1c78ec59e0cb2bd9539d131cf29d45c3fbcf))
* implement user-specific document retrieval and access control ([a8e27c3](https://github.com/GitHamza0206/simba/commit/a8e27c3f5d6eead19cf02418022e547476de72fa))
* improved RAG pipeline with hybrid search advacned ([15ec491](https://github.com/GitHamza0206/simba/commit/15ec491ec3819475a8b38cde0b573fb6732a3ec6))
* migrate to PostgreSQL with pgvector support ([0ea9ffc](https://github.com/GitHamza0206/simba/commit/0ea9ffc7d5a17659efd3d710e4ac5c0406501753))
* MinIO storage ([77a63b7](https://github.com/GitHamza0206/simba/commit/77a63b7cd82cb65d3478423b34047b9a6c84dbf2))
* refactor front api services to use axios instead of request ([efc8cc9](https://github.com/GitHamza0206/simba/commit/efc8cc9238d3535fdd6f91a49882a36b0ca826ca))
* refactor organization routes to use Supabase client and enhance error handling ([1a51e84](https://github.com/GitHamza0206/simba/commit/1a51e84536e531478fbc99a20c43b7c6857cd2df))
* UI UX improvement ([07745c3](https://github.com/GitHamza0206/simba/commit/07745c3e91e1ade1d81e154c91147b29488cebb2))
* update API key management and settings routes ([a92e67b](https://github.com/GitHamza0206/simba/commit/a92e67b78c7a31edb76b085882e6c4d882cea0cf))
* update configuration for LLM and embedding providers, enhance KnowledgeConfigPage ([8559575](https://github.com/GitHamza0206/simba/commit/8559575634a441d52a6edc3e976c4afa30809f88))
* update embedding service and splitter for improved document handling ([ded2ea3](https://github.com/GitHamza0206/simba/commit/ded2ea3a3ffa43e4309487016ba5a2946453b0ab))
* update organization management and settings ([7d86c17](https://github.com/GitHamza0206/simba/commit/7d86c179127a5fe4527be9a3050ae3758e7d48c0))


### 🐛 Bug Fixes

* added .env in ci cd env variables ([95ccffa](https://github.com/GitHamza0206/simba/commit/95ccffa98604520e104d99d8832ec3602d4800ee))
* commented e2e tests ([a2efe49](https://github.com/GitHamza0206/simba/commit/a2efe49a8bb5cebf6e71a2f00391e3df70d03e0e))
* creds in ci ([d1169cf](https://github.com/GitHamza0206/simba/commit/d1169cfa1f9a2b560f2d9e6d97580ba026bc4d0e))
* creds in ci for tests ([19daed9](https://github.com/GitHamza0206/simba/commit/19daed9dfb2e6d848a46a74539bca86d626c3a6f))
* deleted temp file minio ([a868f37](https://github.com/GitHamza0206/simba/commit/a868f373363da35e1024cbbc6ddfce94fa32f724))
* force deleting & markdown preview ([d9e5b69](https://github.com/GitHamza0206/simba/commit/d9e5b69be2c932bd352a033390852987dfc2f69d))
* implement Row Level Security (RLS) policies for organizations and organization members ([75f2da5](https://github.com/GitHamza0206/simba/commit/75f2da5de00caca1997ec2fb23dae81930b70635))
* improve document grading output in grade_node ([cd3101c](https://github.com/GitHamza0206/simba/commit/cd3101cab379ef64a2aa6d28a119c6d441caad2d))
* remove e2e tests ci ([497725f](https://github.com/GitHamza0206/simba/commit/497725fe7c5c0d3f2bc266b28224935a4a94fce2))
* remove notebook ([a69308d](https://github.com/GitHamza0206/simba/commit/a69308d732d91986f607fd884a4ca43631142324))
* remove supabase cli in ci ([bf3a961](https://github.com/GitHamza0206/simba/commit/bf3a96164ec0bd3a8c4876e3cba9de18f2cd8359))
* removed redis cache management from ingestion ([d71a8d5](https://github.com/GitHamza0206/simba/commit/d71a8d5c7081b6a635b3be68e57221fc4ccb7e91))
* UI collection tab creation ([8bc6cfc](https://github.com/GitHamza0206/simba/commit/8bc6cfc014500b5b843c2309b24225d2c37fa2ab))
* update embedding configuration and fix document deletion logic ([925d3e6](https://github.com/GitHamza0206/simba/commit/925d3e6c2f8c3ad3a6435d782b692a4449afd2b4))
* update retrieval method and parameter naming for consistency ([43f0f22](https://github.com/GitHamza0206/simba/commit/43f0f227f6c7570e9c1132584977bf9ef96f3bf6))
* update storage provider and enhance frontend dependencies ([4749723](https://github.com/GitHamza0206/simba/commit/47497231057630403ff9917239787df5749fe6c5))


### 📚 Documentation

* changed doc structure ([44238b0](https://github.com/GitHamza0206/simba/commit/44238b071c8e8287039610b60bc305a5ade82a53))
* chore ([531e60b](https://github.com/GitHamza0206/simba/commit/531e60bb6b9540fa0aeeea9b20e200280c7955eb))
* chore ([014cb0a](https://github.com/GitHamza0206/simba/commit/014cb0a10b4fe44d7ed0b6d57cd89eadb814dd7a))
* cleaned installation ([111392e](https://github.com/GitHamza0206/simba/commit/111392e4e09641d14b2321829523189f2e2736a7))
* fix mint.json structure ([df3f1de](https://github.com/GitHamza0206/simba/commit/df3f1de326d48668ebfff1e1173a7450a31eaa5a))
* fix mint.json structure ([756d657](https://github.com/GitHamza0206/simba/commit/756d65761b23992266cb396e52273ce33846d25a))
* fix mint.json structure ([ce2aea9](https://github.com/GitHamza0206/simba/commit/ce2aea92e552386bf455a3507727768a4974f228))
* fix mint.json structure ([d77cefd](https://github.com/GitHamza0206/simba/commit/d77cefd948ba32534081dad98a239c608efea7f9))
* fixed icons rendering ([5e8424e](https://github.com/GitHamza0206/simba/commit/5e8424ecfa01aa22a8f0cada33cb37f4118f00d2))
* introduction & installation setup ([1ab8049](https://github.com/GitHamza0206/simba/commit/1ab8049555faae7bb7486b9c94baa2d93a01b049))
* remove config ([c0700a0](https://github.com/GitHamza0206/simba/commit/c0700a0c9a859b743c4aea974756e777025495fa))
* removed useless doc ([815dcec](https://github.com/GitHamza0206/simba/commit/815dcec83ce41a4a110cc33ef666e17288fc09dc))
* update introduction ([2fb67cc](https://github.com/GitHamza0206/simba/commit/2fb67cc661d8b1efd7d5e0f24704fd8e361eb012))
* update introduction & assets ([187c1a5](https://github.com/GitHamza0206/simba/commit/187c1a53c52a7f68608e8fc36be9b67bf770f817))
* update structure and added getting started ([7e60063](https://github.com/GitHamza0206/simba/commit/7e600632c796f2f3fdcf75d272571b9bae262f73))


### 🚦 Continuous Integration

* added build phase ([977c6c8](https://github.com/GitHamza0206/simba/commit/977c6c880c9136594df0b8d4c97a5c4241535d4d))
* added conftest to tests ([65065ea](https://github.com/GitHamza0206/simba/commit/65065ea65886c38710d5c6288db2542d93d53aa0))
* improve CI pipeline with robust migration step, PostgreSQL service container, and updated documentation ([a79d016](https://github.com/GitHamza0206/simba/commit/a79d01620d8f7c9e4d637ade34be5891250a1a11))
* removed tests ([d35c8c5](https://github.com/GitHamza0206/simba/commit/d35c8c5ea01e70d2d63063443de8fc25443d22eb))


### 💎 Style

* add copy button ([7f21cba](https://github.com/GitHamza0206/simba/commit/7f21cbaa1eb6354ee6068498530972bc241f6cb6))
* improved chat frame ([33f4684](https://github.com/GitHamza0206/simba/commit/33f4684594667794da6f4644f0af8521b8a1748d))
* improved chat layout ([afafdec](https://github.com/GitHamza0206/simba/commit/afafdec060733f54d7ca8701edd17ccde86fae61))

## [0.4.0](https://github.com/GitHamza0206/simba/compare/v0.3.0...v0.4.0) (2025-03-11)


### ✨ Features

* add Mistral OCR integration with image support ([dc1315f](https://github.com/GitHamza0206/simba/commit/dc1315f941d12be2a3839d56906a2f0ebdcc709b))
* handle multiple documents edit / delete / parse ([310165e](https://github.com/GitHamza0206/simba/commit/310165ece7d40e1b0d35103a0a2cade0d03a3e3c))
* Refactor embedding and parsing services with new EmbeddingService ([b6ef53c](https://github.com/GitHamza0206/simba/commit/b6ef53c1d9f1041e00671ffa369b4e1d5bc716e6))


### 🐛 Bug Fixes

* doc preview with latin-1 ([cf2292d](https://github.com/GitHamza0206/simba/commit/cf2292db54805bb9bbd2b45b732bd3217f546fc6))
* mistral ocr result embedding are removable & images are kept in UI ([c4f10c5](https://github.com/GitHamza0206/simba/commit/c4f10c5ff0901602a46c2df36be91585e284758c))
* Simplify embedding processing and remove multimodal embedding components & Mistral_ocr is removable ([aa2ffdb](https://github.com/GitHamza0206/simba/commit/aa2ffdb100f7def1d499b77ccd4c2ba660ce018e))


### 📚 Documentation

* added first draft of documentation with mintlify ([ee55cd4](https://github.com/GitHamza0206/simba/commit/ee55cd429d6ddee1d75dd206f56d6a1fc0bcca8f))


### 💎 Style

* adding parser badge inside document list ([8fd15b0](https://github.com/GitHamza0206/simba/commit/8fd15b063990af68b0594b665b616585a4f663dd))

## [0.3.0](https://github.com/GitHamza0206/simba/compare/v0.2.0...v0.3.0) (2025-03-07)


### ✨ Features

* ingesting with celery & multiple delete ([0cb4315](https://github.com/GitHamza0206/simba/commit/0cb4315a2b338b4ac0e2c9618a524af6f7fc0743))
* ingestion working with celery ([e9eea7d](https://github.com/GitHamza0206/simba/commit/e9eea7db8d5f4836668d22dc50a8fb3bcd15a7aa))
* refacto retrieval, added abstract class and modulari ([684d51b](https://github.com/GitHamza0206/simba/commit/684d51b897d0d84e0cd66d22914eecaefed1caa0))
* sdk ([c1cb8fe](https://github.com/GitHamza0206/simba/commit/c1cb8fe7fe4c0438815f06acb8fe50e5a808f2b6))


### 🐛 Bug Fixes

* fix multiple document delete ([b080786](https://github.com/GitHamza0206/simba/commit/b0807869bbddf48c883eced0320aa5df3cbc605e))
* modify kwargs in as_retriver function ([bcec99d](https://github.com/GitHamza0206/simba/commit/bcec99daa01e9096817e5ec7602ee628919f92c4))


### 📚 Documentation

* add sdk quickstart in the readme ([b5478af](https://github.com/GitHamza0206/simba/commit/b5478af1331ffa7c8c8841c9b1eb63938b900904))

## [0.2.0](https://github.com/GitHamza0206/simba/compare/v0.1.1...v0.2.0) (2025-03-06)


### ✨ Features

* added clear_store & clean_index ([19fc88c](https://github.com/GitHamza0206/simba/commit/19fc88c22c5a0cf58e5180a16e038a7e3040e0b7))
* adding embeddingManager in simba-client ([0376b70](https://github.com/GitHamza0206/simba/commit/0376b7049f56ea7289e586bfeaaa999416735d34))
* retriever is now in simba-sdk ([63ce7db](https://github.com/GitHamza0206/simba/commit/63ce7db44076d4cb10ad02a9c8333c1f78e7f793))
* retriever.retreive ([05edc21](https://github.com/GitHamza0206/simba/commit/05edc2144df8769d907b6fa74de0bfd940429d0b))
* simba-client is now pip install package ([3daa459](https://github.com/GitHamza0206/simba/commit/3daa459edf81bdb7bd77c24101445c64a2e014be))
* simba-sdk ([9482997](https://github.com/GitHamza0206/simba/commit/94829978b8c8c044a14b068de1a42d0eb69eaa35))
* simba-sdk document ingestion ([a6f4988](https://github.com/GitHamza0206/simba/commit/a6f49885a1f9ce14a350db9854b932710a40112d))


### 🐛 Bug Fixes

* fix retrieve documents returns langchain Document ([fa93fc0](https://github.com/GitHamza0206/simba/commit/fa93fc0e40af941cdce3bec7a0fd460dd25983bf))

## 0.1.0 (2025-03-01)


### ✨ Features

* add framer motion ([9ef44b3](https://github.com/GitHamza0206/simba/commit/9ef44b39ff2aab06cfc1bceb0d359acbc7554545))
* add sources in chat ui frame ([47b8847](https://github.com/GitHamza0206/simba/commit/47b8847eb379aceb4f8c1630315a6a1d4a8b91b4))
* document preview ([7dc5d5e](https://github.com/GitHamza0206/simba/commit/7dc5d5ecf459b9f3d47935819be1187ab4407c7b))
* folder creation ([1101214](https://github.com/GitHamza0206/simba/commit/11012148309318ae6cb37586ba8e13cf35885060))
* implement close chat functionality and update frontend design ([96e94bf](https://github.com/GitHamza0206/simba/commit/96e94bffda13b1c208ea45f1e916e27c84e66728))
* UX multiple document parsing & enabling ([13fbd39](https://github.com/GitHamza0206/simba/commit/13fbd39db4362eddbc67eac249fb63ff36d75d59))


### 🐛 Bug Fixes

* change color of folder ([3627a8b](https://github.com/GitHamza0206/simba/commit/3627a8bffa1df4ed52e24d945f535ce4bc9b255f))
* ci auth ([63d6f4e](https://github.com/GitHamza0206/simba/commit/63d6f4ef2cd0ca00a790bfa59128ac39a64ae750))
* ci relase draft ([b6c9457](https://github.com/GitHamza0206/simba/commit/b6c94574d5d3519e25fcb7a54298344cb7240d0e))
* docker integration & add CI ([660447d](https://github.com/GitHamza0206/simba/commit/660447df6cef3d3dad6bee0aa5d0e050b7146ad6))
* parser keeps file inside folder & same for delete ([7080762](https://github.com/GitHamza0206/simba/commit/7080762878445134a67ab1fd581a433a3f301864))
* release-please hot fix ([5d2e643](https://github.com/GitHamza0206/simba/commit/5d2e643427d6b314208e41f8ab518dd3229e4b06))
* release-please hot fix ([e11487c](https://github.com/GitHamza0206/simba/commit/e11487c7f37a605f040bd625b918d42ea4adc584))


### 🚦 Continuous Integration

* added release-please ([ed4c061](https://github.com/GitHamza0206/simba/commit/ed4c061e447c82d61a7d402ec9fff3fccdd03d1b))

## 1.0.1 - 2025-03-01

### ✨ Features

* Feat: add framer motion. [Hamza Zerouali]

* Feat: add sources in chat ui frame. [Hamza Zerouali]

* Feat: document preview. [Hamza Zerouali]

* Feat: folder creation. [Hamza Zerouali]

* Feat: UX multiple document parsing & enabling. [Hamza Zerouali]

* Feat: implement close chat functionality and update frontend design. [zeroualihamid]

### 🐛 Bug Fixes

* Fix: parser keeps file inside folder & same for delete. [Hamza Zerouali]

* Fix: change color of folder. [Hamza Zerouali]

* Fix: release-please hot fix. [Hamza Zerouali]

* Fix: ci auth. [Hamza Zerouali]

* Fix: docker integration & add CI. [Hamza Zerouali]

* Fix: ci relase draft. [Hamza Zerouali]

### 🔍 Other

* (fix) ci. [Hamza Zerouali]

* (fix) ci. [Hamza Zerouali]

* (feat) CI integration & noxfile. [Hamza Zerouali]

* (feat) ci/cd pipeline. [Hamza Zerouali]

* (fix) docker files multi architecture support & makefile setup. [Hamza Zerouali]

* (doc) improved doc. [Hamza Zerouali]

* (doc) update doc. [Hamza Zerouali]

* (feat) added celery in dependecies. [Hamza Zerouali]

* (feat) simba integrated with notebook. [Hamza Zerouali]

* (fix) removed parserService & refacto. [Hamza Zerouali]

* (doc) improve README & add changelog. [Hamza Zerouali]

* (fix) fix provider error. [Hamza Zerouali]

* (feat) pip install simba. [Hamza Zerouali]

* (feat) add MANIFEST. [Hamza Zerouali]

* (fix) front outside the core. [Hamza Zerouali]

* (feat) simba is pip install. [Hamza Zerouali]

* (refacto) remove /backend  & fixed vector store factory. [Hamza Zerouali]

* (refacto) vector store is now factory. [Hamza Zerouali]

* (feat) doc ingestion is asyncio. [Hamza Zerouali]

* (fix) celery running with simpler command. [Hamza Zerouali]

* (fix) parsing working with celery & new refacto. [Hamza Zerouali]

* (refacto) Add base class for Parsing service. [Hamza Zerouali]

* (fix) config file taken at root dir. [Hamza Zerouali]

* (fix) celery not forced with cpu. [Hamza Zerouali]

* (refacto) fixed import & added isort & autoflake. [Hamza Zerouali]

* (refacto) break services into folders instead. [Hamza Zerouali]

* (refacto) removed core. [Hamza Zerouali]

* (refacto) single poetry env for sdk & core. [Hamza Zerouali]

* (fix) automatic build. [Hamza Zerouali]

* (refacto) factory. [Hamza Zerouali]

* (docs) build setup doc. [Hamza Zerouali]

* (fix) remove DS store. [Hamza Zerouali]

* (fix) config file. [Hamza Zerouali]

* (feat) docker build for CPU & GPU. [Hamza Zerouali]

* (fix) fixing gpu cuda. [mikoba]

* (doc) PH launch. [Hamza Zerouali]

* Mac setup. [Hamza Zerouali]

* (docs) improve readme. [Hamza Zerouali]

* (docs) improve readme. [Hamza Zerouali]

* (docs) improve readme. [Hamza Zerouali]

* (docs) improve readme. [Hamza Zerouali]

* (docs) improve readme. [Hamza Zerouali]

* (fix) fix popple & tesseract issue. [Hamza Zerouali]

* (doc) improve readme. [Hamza Zerouali]

* (doc) improve readme. [Hamza Zerouali]

* (doc) improve readme. [Hamza Zerouali]

* (doc) improve readme. [Hamza Zerouali]

* (doc) improve readme. [Hamza Zerouali]

* (docs) add licence. [Hamza Zerouali]

* (feat) docker working. [Hamza Zerouali]

* (feat) docker backend working. [Hamza Zerouali]

* (doc) modify readme. [Hamza Zerouali]

* (enhancement) toast in UI chatframe & colors for parsing status. [Hamza Zerouali]

* (feat) added chat history in front localstorage. [Hamza Zerouali]

* (fix) parsing sync store with db. [Hamza Zerouali]

* I'll summarize the key changes made to improve the Celery configuration and worker cleanup: Centralized Celery Configuration (celery_config.py): Created a dedicated configuration module Moved all Celery settings into get_celery_config() function Added worker_shutdown_timeout: 10 to give tasks time to cleanup Proper Worker Lifecycle Handling (celery_config.py): Added three signal handlers: complete Centralized Celery App Creation (celery_config.py): Added create_celery_app() function to handle app initialization Created a singleton celery_app instance: None Simplified Task File (parsing_tasks.py): Removed duplicate Celery initialization code Now imports the centralized celery_app Updated decorators to use @celery_app.task instead of @celery.task The main benefits of these changes are: Better resource cleanup during shutdown Centralized configuration management Proper logging of worker lifecycle events Cleaner code organization with separation of concerns More reliable GPU memory cleanup The worker will now properly clean up resources when: The application is stopping Receiving shutdown signals (SIGTERM) Worker process recycling Would you like me to explain any part of these changes in more detail?# Please enter the commit message for your changes. Lines starting. [Hamza Zerouali]

* (do not push) celery problem with multiprocessing. [Hamza Zerouali]

* (feat) add sources in chat app. [Hamza Zerouali]

* (feat) memory to chatbot. [Hamza Zerouali]

* (feat) docling integrated. [Hamza Zerouali]

* (feat) docling integration working. [Hamza Zerouali]

* (feat) celery worker integrated. [Hamza Zerouali]

* (minor) fixes in front. [Hamza Zerouali]

* Added hugging face embeddings. [Hamza Zerouali]

* (minor) removed grader to solve http error. [Hamza Zerouali]

* (refacto) create vectorstore factory & singleton usage. [Hamza Zerouali]

* (fix) kms sync. [Hamza Zerouali]

* (fix) sync db & store & chat. [Hamza Zerouali]

* (refacto) moved SimbaDoc type to /models. [Hamza Zerouali]

* Kms sync with store. [Hamza Zerouali]

* (feat) sync database with store working. [Hamza Zerouali]

* (enhancement) created loader.py replaced hardcoded loading. [Hamza Zerouali]

* (enhance) better rag robust vector store sync. [Hamza Zerouali]

* (feat) chat4u integration. [Hamza Zerouali]

* (refacto) use relative imports in backend. [Hamza Zerouali]

* (refacto) chatbots in /chatbots. [Hamza Zerouali]

* (feat) big improvment backend + frontend. [Hamza Zerouali]

* (fix) git remove services error. [Hamza Zerouali]

* (feat) added configurable database to store data. [Hamza Zerouali]

* (front) upload file button working with new layout. [Hamza Zerouali]

* (feat) ollama running. [Hamza Zerouali]

* (feat) docling integration. [Hamza Zerouali]

* (fix) parsing working, missing file correct ext. [Hamza Zerouali]

* (feat) folder creation backend. [Hamza Zerouali]

* (feat) front: re-index button working. [Hamza Zerouali]

* (feat) /parse working storing + refacto code and lint. [Hamza Zerouali]

* (feat) re-index stores .md file in upload fodler. [Hamza Zerouali]

* (feat) backend : added file storage locally working with refacto code. [Hamza Zerouali]

* (feat) front:  edit document button. [Hamza Zerouali]

* (front) feat: re index button. [Hamza Zerouali]

* Implemented update document. [Hamza Zerouali]

* (front) feat: doc preview working. [Hamza Zerouali]

* (feat) agentic workflow connected to back+front. [Hamza Zerouali]

* (feat) CRUD on vector store KMS. [Hamza Zerouali]

* (feat) : api/get all ingested documents. [Hamza Zerouali]

* Modify git ignore. [Hamza Zerouali]

* Removed data from git remote. [Hamza Zerouali]

* Chore: remove Python cache files and update gitignore. [Hamza Zerouali]

* Module. [Hamza Zerouali]

* Pending. [Hamza Zerouali]

* UI front doc ingestion. [Hamza Zerouali]

* Langsmith prompts management. [Hamza Zerouali]

* Chore: remove .env from git tracking. [Hamza Zerouali]

* Big refacto code. [Hamza Zerouali]

* Module. [Hamza Zerouali]

* Module. [Hamza Zerouali]

* New embedding of pdf files. [zeroualihamid]

* Final embedding. [zeroualihamid]

* New files markdown. [zeroualihamid]

* Fix numerical values in backend. [zeroualihamid]

* Prompt ameliorat. [Ezzahir Fatima]

* Greeting optimisation. [Ezzahir Fatima]

* Fix diplay stream. [zeroualihamid]

* Prompt amelioration. [Ezzahir Fatima]

* Graph modification and conditional branching. [Ezzahir Fatima]

* Stream working and numerical value also. [zeroualihamid]

* Update readme. [Hamza Zerouali]

* Iframe version. [zeroualihamid]

* Fix deploy. [Hamza Zerouali]

* Update deployment. [zeroualihamid]

* Fix dockerfile. [zeroualihamid]

* Updated yaml. [zeroualihamid]

* Update yaml. [zeroualihamid]

* Update compose. [zeroualihamid]

* Deploy2. [zeroualihamid]

* Deploy network. [zeroualihamid]

* Fix StateGraph compile method to remove checkpoint parameterrag_generator memory. [zeroualihamid]

* Refactor RAG generation process and update state management. [zeroualihamid]

  - Enhanced the 'generate' function in flow_functions.py to include message history for improved context in responses.
  - Updated the RAGGenerator class to incorporate chat history in the prompt template and input handling.
  - Adjusted graph compilation in flow_graph.py to utilize a memory checkpointer.
  - Cleaned up state_class.py by removing unnecessary lines and ensuring proper structure.
  - Updated binary files for faiss index and pickle data.


* Fixed dockercompose bug. [zeroualihamid]

* Update react dialog. [zeroualihamid]

* Update dependencies, refactor flow functions, and enhance chat interface. [zeroualihamid]

  - Downgraded Poetry version from 1.8.5 to 1.8.4 in poetry.lock.
  - Removed 'langid' package from project dependencies in pyproject.toml and requirements.txt.
  - Refactored the 'generate' function in flow_functions.py to improve response generation.
  - Updated MemorySaver initialization in flow_graph.py for better configuration.
  - Added a new ChatFrame component for improved chat interface in the frontend.
  - Updated package-lock.json and package.json to include new Radix UI dependencies.
  - Cleaned up unused imports and adjusted component structures for better readability.


* Update dependencies and refactor flow functions for improved response generation. [zeroualihamid]

  - Updated Poetry version from 1.8.4 to 1.8.5 and added 'langid' package (v1.1.6) to project dependencies.
  - Refactored the 'generate' function in flow_functions.py to utilize the React agent for asynchronous message processing.
  - Adjusted MemorySaver initialization in flow_graph.py and ensured proper graph compilation.
  - Cleaned up unused imports and comments in rag_generator_agent.py and state_class.py.
  - Updated .gitignore to ensure proper exclusion of __pycache__ directory.
  - Modified requirements.txt to include 'langid' and 'googletrans' packages.


* Updated readme. [GitHamza0206]

* Dockerised version. [GitHamza0206]

* Stable back + front. [zeroualihamid]

* Front is streaming. [zeroualihamid]

* Commit1. [zeroualihamid]

* Remove api from gitignore. [zeroualihamid]

* Working app1. [zeroualihamid]

* Fix poetry env for windows. [zeroualihamid]

* Changed structure and working. [GitHamza0206]

* Fix poetry. [GitHamza0206]

* Chat routes. [zeroualihamid]

* Chaged chroma to faiss + refacto. [GitHamza0206]

* Added poetry config. [GitHamza0206]

* Improved front end. [GitHamza0206]

* Hamid updates. [zeroualihamid]

* Change routes add world 2. [zeroualihamid]

* Setup backend arch + frontend. [GitHamza0206]

* Readme. [GitHamza0206]

* Update README.md. [Hamza Zerouali]

* Update README.md. [Hamza Zerouali]

* Update README.md. [Hamza Zerouali]

* Initial commit. [Hamza Zerouali]


## v1.0.1 (2025-01-14)

### 🔍 Other

* (front) feat: doc preview working. [Hamza Zerouali]


## v1.0.0 (2025-01-13)

### ✨ Features

* Feat: implement close chat functionality and update frontend design. [zeroualihamid]

### 🔍 Other

* (feat) agentic workflow connected to back+front. [Hamza Zerouali]

* (feat) CRUD on vector store KMS. [Hamza Zerouali]

* (feat) : api/get all ingested documents. [Hamza Zerouali]

* Modify git ignore. [Hamza Zerouali]

* Removed data from git remote. [Hamza Zerouali]

* Chore: remove Python cache files and update gitignore. [Hamza Zerouali]

* Module. [Hamza Zerouali]

* Pending. [Hamza Zerouali]

* UI front doc ingestion. [Hamza Zerouali]

* Langsmith prompts management. [Hamza Zerouali]

* Chore: remove .env from git tracking. [Hamza Zerouali]

* Big refacto code. [Hamza Zerouali]

* Module. [Hamza Zerouali]

* Module. [Hamza Zerouali]

* New embedding of pdf files. [zeroualihamid]

* Final embedding. [zeroualihamid]

* New files markdown. [zeroualihamid]

* Fix numerical values in backend. [zeroualihamid]

* Prompt ameliorat. [Ezzahir Fatima]

* Greeting optimisation. [Ezzahir Fatima]

* Fix diplay stream. [zeroualihamid]

* Prompt amelioration. [Ezzahir Fatima]

* Graph modification and conditional branching. [Ezzahir Fatima]

* Stream working and numerical value also. [zeroualihamid]

* Update readme. [Hamza Zerouali]

* Iframe version. [zeroualihamid]

* Fix deploy. [Hamza Zerouali]

* Update deployment. [zeroualihamid]

* Fix dockerfile. [zeroualihamid]

* Updated yaml. [zeroualihamid]

* Update yaml. [zeroualihamid]

* Update compose. [zeroualihamid]

* Deploy2. [zeroualihamid]

* Deploy network. [zeroualihamid]

* Fix StateGraph compile method to remove checkpoint parameterrag_generator memory. [zeroualihamid]

* Refactor RAG generation process and update state management. [zeroualihamid]

  - Enhanced the 'generate' function in flow_functions.py to include message history for improved context in responses.
  - Updated the RAGGenerator class to incorporate chat history in the prompt template and input handling.
  - Adjusted graph compilation in flow_graph.py to utilize a memory checkpointer.
  - Cleaned up state_class.py by removing unnecessary lines and ensuring proper structure.
  - Updated binary files for faiss index and pickle data.


* Fixed dockercompose bug. [zeroualihamid]

* Update react dialog. [zeroualihamid]

* Update dependencies, refactor flow functions, and enhance chat interface. [zeroualihamid]

  - Downgraded Poetry version from 1.8.5 to 1.8.4 in poetry.lock.
  - Removed 'langid' package from project dependencies in pyproject.toml and requirements.txt.
  - Refactored the 'generate' function in flow_functions.py to improve response generation.
  - Updated MemorySaver initialization in flow_graph.py for better configuration.
  - Added a new ChatFrame component for improved chat interface in the frontend.
  - Updated package-lock.json and package.json to include new Radix UI dependencies.
  - Cleaned up unused imports and adjusted component structures for better readability.


* Update dependencies and refactor flow functions for improved response generation. [zeroualihamid]

  - Updated Poetry version from 1.8.4 to 1.8.5 and added 'langid' package (v1.1.6) to project dependencies.
  - Refactored the 'generate' function in flow_functions.py to utilize the React agent for asynchronous message processing.
  - Adjusted MemorySaver initialization in flow_graph.py and ensured proper graph compilation.
  - Cleaned up unused imports and comments in rag_generator_agent.py and state_class.py.
  - Updated .gitignore to ensure proper exclusion of __pycache__ directory.
  - Modified requirements.txt to include 'langid' and 'googletrans' packages.


* Updated readme. [GitHamza0206]

* Dockerised version. [GitHamza0206]

* Stable back + front. [zeroualihamid]

* Front is streaming. [zeroualihamid]

* Commit1. [zeroualihamid]

* Remove api from gitignore. [zeroualihamid]

* Working app1. [zeroualihamid]

* Fix poetry env for windows. [zeroualihamid]

* Changed structure and working. [GitHamza0206]

* Fix poetry. [GitHamza0206]

* Chat routes. [zeroualihamid]

* Chaged chroma to faiss + refacto. [GitHamza0206]

* Added poetry config. [GitHamza0206]

* Improved front end. [GitHamza0206]

* Hamid updates. [zeroualihamid]

* Change routes add world 2. [zeroualihamid]

* Setup backend arch + frontend. [GitHamza0206]

* Readme. [GitHamza0206]

* Update README.md. [Hamza Zerouali]

* Update README.md. [Hamza Zerouali]

* Update README.md. [Hamza Zerouali]

* Initial commit. [Hamza Zerouali]

* Remove nested Git repositories. [zeroualihamid]

* Save work. [zeroualihamid]

* Memory retreive. [zeroualihamid]

* Initial commit. [Ezzahir Fatima]
