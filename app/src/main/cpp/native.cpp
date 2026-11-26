#include <jni.h>
#include <llama.h>
#include <atomic>
#include <string>
#include <vector>
#include <algorithm>
static llama_model *model=nullptr;
static std::atomic<bool> stopped{false};
static std::string str(JNIEnv* e,jbyteArray a){std::string s(e->GetArrayLength(a),'\0');e->GetByteArrayRegion(a,0,s.size(),reinterpret_cast<jbyte*>(s.data()));return s;}
static void fail(JNIEnv* e,const char* s){e->ThrowNew(e->FindClass("java/lang/IllegalStateException"),s);}
extern "C" JNIEXPORT void JNICALL Java_com_solune_app_EngineService_nativeStop(JNIEnv*,jclass){stopped=true;}
extern "C" JNIEXPORT void JNICALL Java_com_solune_app_EngineService_nativeLoad(JNIEnv* e,jclass,jbyteArray path){static bool init=false;if(!init){llama_backend_init();init=true;}if(model){llama_model_free(model);model=nullptr;}auto p=llama_model_default_params();p.n_gpu_layers=0;p.use_mmap=true;model=llama_model_load_from_file(str(e,path).c_str(),p);if(!model)fail(e,"Не удалось открыть GGUF");}
extern "C" JNIEXPORT void JNICALL Java_com_solune_app_EngineService_nativeGenerate(JNIEnv* e,jclass,jbyteArray input,jint max,jint threads,jobject cb){if(!model){fail(e,"Модель не загружена");return;}stopped=false;auto prompt=str(e,input);auto vocab=llama_model_get_vocab(model);int n=-llama_tokenize(vocab,prompt.data(),prompt.size(),nullptr,0,true,true);if(n<=0||n>=1920){fail(e,"Контекст слишком длинный");return;}std::vector<llama_token> tokens(n);llama_tokenize(vocab,prompt.data(),prompt.size(),tokens.data(),n,true,true);auto p=llama_context_default_params();p.n_ctx=2048;p.n_batch=256;p.n_threads=threads;p.n_threads_batch=threads;auto ctx=llama_init_from_model(model,p);if(!ctx){fail(e,"Недостаточно памяти для контекста");return;}auto sm=llama_sampler_chain_init(llama_sampler_chain_default_params());llama_sampler_chain_add(sm,llama_sampler_init_greedy());auto meth=e->GetMethodID(e->GetObjectClass(cb),"piece","([B)V");bool ok=true;for(int i=0;i<n&&!stopped;i+=256){auto b=llama_batch_get_one(tokens.data()+i,std::min(256,n-i));if(llama_decode(ctx,b)){ok=false;break;}}for(int i=0;ok&&!stopped&&i<std::min((int)max,2048-n-1);i++){auto t=llama_sampler_sample(sm,ctx,-1);if(llama_vocab_is_eog(vocab,t))break;char buf[1024];int len=llama_token_to_piece(vocab,t,buf,sizeof(buf),0,false);if(len>0){auto a=e->NewByteArray(len);e->SetByteArrayRegion(a,0,len,(jbyte*)buf);e->CallVoidMethod(cb,meth,a);e->DeleteLocalRef(a);if(e->ExceptionCheck())break;}if(llama_decode(ctx,llama_batch_get_one(&t,1))){ok=false;break;}}llama_sampler_free(sm);llama_free(ctx);if(!ok&&!e->ExceptionCheck())fail(e,"Ошибка вычисления модели");}
