import torch
from loss import *
from network import BATCH_SIZE, LATENT
from helpers import save_graph, save_images
import logging

def train_step(X, generator, discriminator, gen_optim, disc_optim, device):
    noise = torch.randn(BATCH_SIZE, LATENT, 1, 1, device=device)
    X = X.to(device)

    ######################
    ##Update Discriminator
    ######################

    #On real images
    disc_optim.zero_grad()

    real_output = discriminator(X)

    real_loss = -1 * torch.mean(torch.log(real_output))
    real_loss.backward()
    D_x = real_output.mean().item()
    
    #On fake images
    generated_images = generator(noise)
    fake_output = discriminator(generated_images.detach())

    fake_loss = -1 * torch.mean(torch.log(1 - fake_output))
    fake_loss.backward()
    D_G_z1 = fake_output.mean().item()

    disc_loss = real_loss + fake_loss
    disc_optim.step()

    ###################
    ##Update Generator
    ###################
    gen_optim.zero_grad()

    fake_output = discriminator(generated_images)   #Create new fake_out so gradients can be updated
    gen_loss = -1 * torch.mean(torch.log(fake_output)) 

    gen_loss.backward()
    gen_optim.step()
    D_G_z2 = fake_output.mean().item()
    
    return gen_loss, disc_loss, D_x, (D_G_z1, D_G_z2)

def train(epochs, dataloader, generator, discriminator, gen_optim, disc_optim):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Using {} device".format(device))

    fixed_noise = torch.randn(64, LATENT, 1, 1, device=device)
    size = len(dataloader)
    generator.train()
    discriminator.train()

    G_losses = []
    D_losses = []

    for epoch in range(epochs):
        print("\n--\n")
        for batch, X in enumerate(dataloader):
            Gl, Dl, D_x, D_G_z= train_step(X, generator, discriminator, gen_optim, disc_optim, device)

            G_losses.append(Gl.item())
            D_losses.append(Dl.item())

            if batch % 10 == 0:
                out = f"[{epoch+1:d}/{epochs:d}][{batch:d}/{size:d}]\tLoss_D: {Dl.item():.4f}\tLoss_G: {Gl.item():.4f} \
                    \tD(x): {D_x:.4f}\tD(G(z)): {D_G_z[0]:.4f}, {D_G_z[1]:.4f}"

                print(out)
                logging.info(out)

                        # % (epoch+1, epochs, batch, size, Dl.item(), Gl.item(), D_x, D_G_z[0], D_G_z[1])
                # print("[%d/%d][%d/%d]\tLoss_D: %.4f\tLoss_G: %.4f\tD(x): %.4f\tD(G(z)): %.4f, %.4f"
                #         % (epoch+1, epochs, batch, size, Dl.item(), Gl.item(), D_x, D_G_z[0], D_G_z[1]))

        save_graph("G and D loss", "Iterations", "Loss", epoch, G_losses, "G", D_losses, "D")
        
        with torch.no_grad():
            test_batch = generator(fixed_noise).detach().cpu()
        save_images(test_batch, epoch, n_cols=8)
        
            

    return