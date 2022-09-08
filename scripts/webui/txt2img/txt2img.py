from util.imports import *
from util.misc_diffusion import *
from util.torch_gc import *
from util.seed_to_int import *
from util.process_images import *

#@retry(RuntimeError, tries=3)
def txt2img(prompt: str, ddim_steps: int, sampler_name: str, realesrgan_model_name: str,
            n_iter: int, batch_size: int, cfg_scale: float, seed: Union[int, str, None],
            height: int, width: int, separate_prompts:bool = False, normalize_prompt_weights:bool = True,
            save_individual_images: bool = True, save_grid: bool = True, group_by_prompt: bool = True,
            save_as_jpg: bool = True, use_GFPGAN: bool = True, use_RealESRGAN: bool = True, 
            RealESRGAN_model: str = "RealESRGAN_x4plus_anime_6B", fp = None, variant_amount: float = None, 
            variant_seed: int = None, ddim_eta:float = 0.0, write_info_files:bool = True):

	outpath = defaults.general.outdir_txt2img or defaults.general.outdir or "outputs/txt2img-samples"

	err = False
	seed = seed_to_int(seed)

	#prompt_matrix = 0 in toggles
	#normalize_prompt_weights = 1 in toggles
	#skip_save = 2 not in toggles
	#save_grid = 3 not in toggles
	#sort_samples = 4 in toggles
	#write_info_files = 5 in toggles
	#jpg_sample = 6 in toggles
	#use_GFPGAN = 7 in toggles
	#use_RealESRGAN = 8 in toggles

	if sampler_name == 'PLMS':
		sampler = PLMSSampler(st.session_state["model"])
	elif sampler_name == 'DDIM':
		sampler = DDIMSampler(st.session_state["model"])
	elif sampler_name == 'k_dpm_2_a':
		sampler = KDiffusionSampler(st.session_state["model"],'dpm_2_ancestral')
	elif sampler_name == 'k_dpm_2':
		sampler = KDiffusionSampler(st.session_state["model"],'dpm_2')
	elif sampler_name == 'k_euler_a':
		sampler = KDiffusionSampler(st.session_state["model"],'euler_ancestral')
	elif sampler_name == 'k_euler':
		sampler = KDiffusionSampler(st.session_state["model"],'euler')
	elif sampler_name == 'k_heun':
		sampler = KDiffusionSampler(st.session_state["model"],'heun')
	elif sampler_name == 'k_lms':
		sampler = KDiffusionSampler(st.session_state["model"],'lms')
	else:
		raise Exception("Unknown sampler: " + sampler_name)

	def init():
		pass

	def sample(init_data, x, conditioning, unconditional_conditioning, sampler_name):
		samples_ddim, _ = sampler.sample(S=ddim_steps, conditioning=conditioning, batch_size=int(x.shape[0]), shape=x[0].shape, verbose=False, unconditional_guidance_scale=cfg_scale,
                                                 unconditional_conditioning=unconditional_conditioning, eta=ddim_eta, x_T=x, img_callback=generation_callback,
                                         log_every_t=int(defaults.general.update_preview_frequency))

		return samples_ddim

	#try:
	output_images, seed, info, stats = process_images(
                outpath=outpath,
                func_init=init,
                func_sample=sample,
                prompt=prompt,
                seed=seed,
                sampler_name=sampler_name,
                save_grid=save_grid,
                batch_size=batch_size,
                n_iter=n_iter,      
                steps=ddim_steps,   
                cfg_scale=cfg_scale,	
                width=width,
                height=height,
                prompt_matrix=separate_prompts,
                use_GFPGAN=use_GFPGAN,
                use_RealESRGAN=use_RealESRGAN,
                realesrgan_model_name=realesrgan_model_name,
                fp=fp,
                ddim_eta=ddim_eta,
                normalize_prompt_weights=normalize_prompt_weights,
                save_individual_images=save_individual_images,
                sort_samples=group_by_prompt,
                write_info_files=write_info_files,
                jpg_sample=save_as_jpg,
                variant_amount=variant_amount,
                variant_seed=variant_seed,
        )

	del sampler

	return output_images, seed, info, stats